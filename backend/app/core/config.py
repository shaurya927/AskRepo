from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AskRepo"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/askrepo"
    GITHUB_TOKEN: str | None = None
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    MAX_REPOSITORY_SIZE_MB: int = 50
    MAX_FILE_COUNT: int = 2000
    MAX_FILE_SIZE_MB: int = 1
    MAX_AI_REQUESTS_PER_DAY: int = 20
    MAX_ANALYSES_PER_DAY: int = 3
    TEMP_REPOSITORY_PATH: str = "./tmp/repos"
    VECTOR_INDEX_PATH: str = "./tmp/indexes"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

@lru_cache
def get_settings():
    return Settings()
