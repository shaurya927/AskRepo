"""Tests for application configuration."""

from app.core.config import Settings


class TestSettings:
    def test_defaults(self):
        """Settings should have sensible defaults."""
        s = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        assert s.APP_NAME == "AskRepo"
        assert s.APP_VERSION == "0.1.0"
        assert s.MAX_REPOSITORY_SIZE_MB == 50
        assert s.MAX_FILE_COUNT == 2000
        assert s.MAX_FILE_SIZE_MB == 1
        assert s.MAX_AI_REQUESTS_PER_DAY == 20
        assert s.MAX_ANALYSES_PER_DAY == 3

    def test_cors_origins_default(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        assert "http://localhost:5173" in s.BACKEND_CORS_ORIGINS

    def test_optional_fields(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        assert s.GITHUB_TOKEN is None
        assert s.LLM_API_KEY is None
