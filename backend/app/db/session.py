import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database Engine
#
# The engine is the connection to the database. It manages a connection pool.
#
# pool_pre_ping=True:
#   Before using a connection from the pool, SQLAlchemy sends a lightweight
#   "ping" query. If the DB server restarted and the connection is stale,
#   this prevents a cryptic error — the pool discards the dead connection
#   and creates a fresh one.
#
# pool_size=10:
#   Number of connections maintained in the pool at all times.
#   10 concurrent users = 10 connections in use simultaneously.
#
# max_overflow=20:
#   Additional connections allowed when pool_size is exhausted.
#   Total max = pool_size + max_overflow = 30 connections.
#
# echo=settings.DEBUG:
#   Logs every SQL query when DEBUG=True. Essential for development.
#   NEVER enable in production (leaks data, floods logs).
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
)

# ---------------------------------------------------------------------------
# Session Factory
#
# SessionLocal() creates a new database session.
#
# autocommit=False: Transactions must be committed manually.
#                   This gives us control — we can rollback on error.
# autoflush=False:  Don't automatically sync pending changes to DB before
#                   queries. Gives us control over when flushes happen.
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per HTTP request.

    This function is a generator — it yields the session and then the
    finally block runs after the request is complete (whether or not
    an exception occurred).

    Lifecycle per request:
        1. db = SessionLocal()    ← new session created
        2. yield db               ← request handler runs with this session
        3. (exception?)           ← db.rollback() called on error
        4. db.close()             ← connection returned to pool

    This pattern guarantees:
        - No session is shared between requests (thread-safe)
        - Sessions are always closed even if an exception is raised
        - Failed transactions are rolled back before closing

    Usage in route handlers:
        from fastapi import Depends
        from sqlalchemy.orm import Session
        from app.api.deps import get_db

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
