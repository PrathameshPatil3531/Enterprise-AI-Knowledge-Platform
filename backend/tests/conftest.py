"""
tests/conftest.py — Pytest Fixtures

Fixtures defined here are automatically available to ALL test files.
No imports needed in test files — pytest discovers them automatically.

HOW TO RUN TESTS:
    # From the backend/ directory with venv activated:
    pytest tests/ -v

    # Run only auth tests:
    pytest tests/test_auth.py -v

    # Run with coverage report:
    pytest tests/ --cov=app --cov-report=term-missing

PREREQUISITES:
    - PostgreSQL running (docker compose up -d postgres)
    - .env file configured (copy from .env.example)
    - `pip install pytest pytest-asyncio httpx` (included in requirements.txt)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# ---------------------------------------------------------------------------
# Test Database Setup
#
# WHY a separate test database?
# - Tests should NEVER run against the production or development database.
# - Tests create, modify, and delete data — they must be isolated.
#
# Strategy: Use the same DATABASE_URL but a different DB name.
# Alternatively, use SQLite in-memory for pure unit tests (no PostgreSQL needed).
#
# For now: We use a real PostgreSQL test DB (requires docker compose up -d postgres).
# The test DB name is derived from the main DB URL by appending "_test".
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    f"/{settings.DATABASE_URL.split('/')[-1]}",  # Remove DB name
    f"/{settings.DATABASE_URL.split('/')[-1]}_test",  # Append _test
)

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create all tables in the test database before any tests run.
    Drop all tables after all tests complete.

    scope="session": Runs once per pytest session (not once per test).
    autouse=True: Applied automatically to all tests.
    """
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db():
    """
    Provide a test database session that is rolled back after each test.

    scope="function": A fresh state for each individual test function.

    WHY rollback instead of delete?
    Rollback is faster than DELETE and guarantees a clean slate without
    leaving orphaned rows if a test crashes mid-way.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    """
    Provide a FastAPI TestClient with the test database session injected.

    This overrides the `get_db` dependency so routes use the test DB session
    (with rollback isolation) instead of the production session.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass  # Rollback handled by the `db` fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """
    Fixture that registers a test user and returns their credentials + response.
    Used by tests that need a pre-existing user.
    """
    user_data = {
        "email": "testuser@example.com",
        "password": "TestPass1",
        "full_name": "Test User",
    }
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    return {"credentials": user_data, "user": response.json()}


@pytest.fixture
def auth_headers(client, registered_user):
    """
    Fixture that logs in the registered user and returns auth headers.
    Used by tests that need a protected endpoint.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": registered_user["credentials"]["email"],
            "password": registered_user["credentials"]["password"],
        },
    )
    assert response.status_code == 200
    access_token = response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
