"""Tests for AI Gateway."""

import pytest
from unittest.mock import MagicMock

from app.services.ai.gateway import AIGateway, GeminiProvider


class TestAIGateway:

    def test_raises_without_api_key(self):
        settings = MagicMock()
        settings.GOOGLE_API_KEY = ""
        gateway = AIGateway(settings)
        with pytest.raises(ValueError, match="No AI API key"):
            gateway.get_provider()

    def test_uses_byok_key(self):
        settings = MagicMock()
        settings.GOOGLE_API_KEY = ""
        settings.AI_MODEL = "gemini-2.5-flash"
        gateway = AIGateway(settings)
        # Should not raise with BYOK key
        provider = gateway.get_provider(byok_key="test-key")
        assert isinstance(provider, GeminiProvider)

    def test_uses_platform_key(self):
        settings = MagicMock()
        settings.GOOGLE_API_KEY = "platform-key"
        settings.AI_MODEL = "gemini-2.5-flash"
        gateway = AIGateway(settings)
        provider = gateway.get_provider()
        assert isinstance(provider, GeminiProvider)

    def test_byok_takes_precedence(self):
        settings = MagicMock()
        settings.GOOGLE_API_KEY = "platform-key"
        settings.AI_MODEL = "gemini-2.5-flash"
        gateway = AIGateway(settings)
        # BYOK should be used instead of platform
        provider = gateway.get_provider(byok_key="user-key")
        assert provider.name() == "gemini:gemini-2.5-flash"

    def test_provider_name(self):
        settings = MagicMock()
        settings.GOOGLE_API_KEY = "key"
        settings.AI_MODEL = "gemini-2.5-flash"
        gateway = AIGateway(settings)
        provider = gateway.get_provider()
        assert "gemini" in provider.name()
