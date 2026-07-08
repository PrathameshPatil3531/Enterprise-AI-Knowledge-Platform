from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base class.

    WHY a custom Base class?
    - All ORM models inherit from this Base
    - Alembic uses Base.metadata to detect table changes and generate migrations
    - Centralizes any shared table configuration (e.g., naming conventions)

    IMPORTANT: This file must NOT import any models.
    Models import Base, not the other way around.
    All models are imported in app/models/__init__.py for Alembic discovery.
    """
    pass
