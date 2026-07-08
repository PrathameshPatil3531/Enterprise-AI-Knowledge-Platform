from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Reads values from environment variables and .env file.
    Pydantic validates all types at startup — the app fails immediately
    if a required variable is missing or has the wrong type.

    This is the 12-Factor App methodology: Config from the environment.
    (https://12factor.net/config)
    """

    # --------------------------------------------------------------------------
    # Application
    # --------------------------------------------------------------------------
    APP_NAME: str = "Enterprise AI Knowledge Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False

    # --------------------------------------------------------------------------
    # Security
    # --------------------------------------------------------------------------
    # REQUIRED — generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15   # Short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7      # Long-lived refresh token
    ALGORITHM: str = "HS256"               # JWT signing algorithm

    # --------------------------------------------------------------------------
    # Database (PostgreSQL)
    # --------------------------------------------------------------------------
    # Format: postgresql://user:password@host:port/dbname
    DATABASE_URL: str

    # --------------------------------------------------------------------------
    # Redis
    # --------------------------------------------------------------------------
    # Format: redis://:password@host:port/db_number
    REDIS_URL: str

    # --------------------------------------------------------------------------
    # Qdrant (Vector Database)
    # --------------------------------------------------------------------------
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "knowledge_base"

    # --------------------------------------------------------------------------
    # LLM (OpenAI or OpenAI-compatible)
    # --------------------------------------------------------------------------
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # --------------------------------------------------------------------------
    # Embeddings
    # --------------------------------------------------------------------------
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Local SentenceTransformer model
    EMBEDDING_DIMENSION: int = 384               # Output vector size for above model

    # --------------------------------------------------------------------------
    # CORS — which frontend origins are allowed to call this API
    # --------------------------------------------------------------------------
    # In .env, set as comma-separated: http://localhost:5173,https://yourdomain.com
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    # --------------------------------------------------------------------------
    # File Upload
    # --------------------------------------------------------------------------
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Allow ALLOWED_ORIGINS to be set as a comma-separated string in .env."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# ---------------------------------------------------------------------------
# Singleton instance — import `settings` everywhere you need config.
#
# Usage:
#   from app.core.config import settings
#   print(settings.DATABASE_URL)
# ---------------------------------------------------------------------------
settings = Settings()
