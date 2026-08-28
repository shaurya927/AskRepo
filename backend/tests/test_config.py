"""Tests for application configuration."""

from app.core.config import Settings


class TestSettings:
    def test_defaults(self):
        """Settings should have sensible defaults."""
        s = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        assert s.APP_NAME == "AskRepo"
        assert s.APP_VERSION == "0.5.0"
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
        assert s.GITHUB_TOKEN is None or s.GITHUB_TOKEN == ""  # May be set via .env
        assert isinstance(s.GOOGLE_API_KEY, str)  # May be set via .env

    def test_phase3_defaults(self):
        s = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        assert s.AI_MODEL == "gemini-2.5-flash"
        assert s.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
        assert s.VECTOR_SEARCH_TOP_K == 15
        assert s.MAX_TOKENS_PER_REQUEST == 4096
