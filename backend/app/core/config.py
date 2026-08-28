"""Application configuration via environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AskRepo"
    APP_VERSION: str = "0.5.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/askrepo"

    # GitHub
    GITHUB_TOKEN: str | None = None

    # Repository limits
    MAX_REPOSITORY_SIZE_MB: int = 50
    MAX_FILE_COUNT: int = 2000
    MAX_FILE_SIZE_MB: int = 1

    # Usage limits
    MAX_AI_REQUESTS_PER_DAY: int = 20
    MAX_ANALYSES_PER_DAY: int = 3

    # Storage
    TEMP_REPOSITORY_PATH: str = "./tmp/repos"
    VECTOR_INDEX_PATH: str = "./data/indices"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # AI Gateway — Phase 3
    GOOGLE_API_KEY: str = ""
    AI_MODEL: str = "gemini-2.5-flash"
    MAX_TOKENS_PER_REQUEST: int = 4096

    # Embeddings — Phase 3
    EMBEDDING_MODEL: str = "gemini-embedding-2"
    EMBEDDING_BATCH_SIZE: int = 64

    # Vector search — Phase 3
    VECTOR_SEARCH_TOP_K: int = 15

    # Git Archaeology — Phase 5
    GIT_CLONE_DEPTH: int = 200
    GIT_MAX_DIFF_SIZE: int = 50000

    # Production Hardening — Phase 7
    LOG_LEVEL: str = "INFO"
    CLEANUP_MAX_AGE_HOURS: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings():
    return Settings()
