"""
Alembic Environment Configuration.

This file is run by Alembic when generating or applying migrations.
It configures:
  - The database URL (from environment variables, never hardcoded)
  - The metadata Alembic compares against to detect changes
  - Offline and online migration modes

IMPORTANT: All models must be imported (via app.models) before migrations
are generated, otherwise Alembic won't know the tables exist.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------------------------
# Make sure the backend/ directory is on sys.path so we can import app.*
# This is needed when running: alembic revision --autogenerate
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env file so DATABASE_URL is available as an environment variable
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Import Base and ALL models.
#
# Alembic compares Base.metadata (Python model definitions) against
# the actual database schema to generate migrations.
#
# If a model is not imported here, Alembic will NOT generate a migration
# for it — even if the table is defined in the models/ folder.
# ---------------------------------------------------------------------------
from app.db.base import Base
from app.models import *  # noqa: F401, F403 — imports all models

# ---------------------------------------------------------------------------
# Alembic Config
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url from the environment variable.
# This is critical: database credentials must NEVER be in alembic.ini.
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Ensure .env file exists or environment is configured."
    )
config.set_main_option("sqlalchemy.url", database_url)

# Setup Python logging as configured in alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This metadata is what Alembic uses to detect schema differences
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    Useful when you want a DBA to review SQL before applying it in production.

    Command: alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,        # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Connects directly to the database and applies migrations.
    Used in development (alembic upgrade head) and CI/CD pipelines.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling for migrations (one-shot operation)
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# Alembic determines which mode to use based on how it's invoked
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
