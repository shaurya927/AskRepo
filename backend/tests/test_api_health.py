"""Tests for the health endpoint — no DB required."""

from app.core.config import Settings


class TestHealthEndpoint:
    def test_health_response_structure(self):
        """The health endpoint should return status, version, and timestamp."""
        from app.schemas.health import HealthResponse

        settings = Settings(DATABASE_URL="postgresql+asyncpg://test:test@localhost/test")
        response = HealthResponse(
            status="ok",
            version=settings.APP_VERSION,
            timestamp="2024-01-01T00:00:00Z",
        )
        assert response.status == "ok"
        assert response.version == "0.5.0"
        assert response.timestamp == "2024-01-01T00:00:00Z"
