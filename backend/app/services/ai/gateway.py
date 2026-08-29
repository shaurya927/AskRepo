"""AI Gateway — provider abstraction for LLM inference."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class AIProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        ...

    @abstractmethod
    async def generate_stream(self, prompt: str, system: str = "", max_tokens: int = 4096) -> AsyncIterator[str]:
        ...

    @abstractmethod
    def name(self) -> str:
        ...


FALLBACK_CHAIN = {
    "gemini-3.7-flash": "gemini-3.6-flash",
    "gemini-3.6-flash": "gemini-3.5-flash",
    "gemini-3.5-flash": "gemini-3.5-flash-lite",
    "gemini-3.5-flash-lite": "gemini-3.1-flash-lite",
    "gemini-3.1-flash": "gemini-3.1-flash-lite",
    "gemini-2.5-pro": "gemini-2.5-flash",
    "gemini-2.5-flash": "gemini-2.5-flash-lite",
    "gemini-1.5-pro": "gemini-1.5-flash",
    "gemini-1.5-flash": "gemini-1.5-flash-8b",
}

class GeminiProvider(AIProvider):
    """Google Gemini provider using google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-3.5-flash-lite"):
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system if system else None,
            max_output_tokens=max_tokens,
            temperature=0.3,
        )
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            if "429" in str(e) and self._model in FALLBACK_CHAIN:
                fallback = FALLBACK_CHAIN[self._model]
                import logging
                logging.getLogger(__name__).warning(f"Rate limited on {self._model}, falling back to {fallback}")
                self._model = fallback
                return await self.generate(prompt, system, max_tokens)
            raise

    async def generate_stream(self, prompt: str, system: str = "", max_tokens: int = 4096) -> AsyncIterator[str]:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system if system else None,
            max_output_tokens=max_tokens,
            temperature=0.3,
        )
        try:
            response = await self._client.aio.models.generate_content_stream(
                model=self._model,
                contents=prompt,
                config=config,
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            if "429" in str(e) and self._model in FALLBACK_CHAIN:
                fallback = FALLBACK_CHAIN[self._model]
                import logging
                logging.getLogger(__name__).warning(f"Rate limited on {self._model}, falling back to {fallback}")
                self._model = fallback
                # Recursively call generate_stream with the new model
                async for chunk in self.generate_stream(prompt, system, max_tokens):
                    yield chunk
            else:
                raise

    def name(self) -> str:
        return f"gemini:{self._model}"


class AIGateway:
    """Gateway that selects and manages AI providers."""

    def __init__(self, settings):
        self._settings = settings
        self._default_provider: AIProvider | None = None

    def get_provider(self, byok_key: str | None = None) -> AIProvider:
        """Get an AI provider. BYOK key takes precedence."""
        api_key = byok_key or self._settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError(
                "No AI API key configured. Set GOOGLE_API_KEY in .env or provide your own key."
            )
        return GeminiProvider(api_key=api_key, model=self._settings.AI_MODEL)

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int | None = None,
        byok_key: str | None = None,
    ) -> tuple[str, str]:
        """Generate a response. Returns (text, model_name)."""
        provider = self.get_provider(byok_key)
        tokens = max_tokens or self._settings.MAX_TOKENS_PER_REQUEST
        text = await provider.generate(prompt, system, tokens)
        return text, provider.name()

    async def generate_stream(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int | None = None,
        byok_key: str | None = None,
    ) -> tuple[AsyncIterator[str], str]:
        """Generate a streaming response. Returns (stream, model_name)."""
        provider = self.get_provider(byok_key)
        tokens = max_tokens or self._settings.MAX_TOKENS_PER_REQUEST
        stream = provider.generate_stream(prompt, system, tokens)
        return stream, provider.name()
