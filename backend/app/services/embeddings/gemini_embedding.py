import os
import numpy as np
from app.services.embeddings.embedding_service import EmbeddingService
from google import genai
from app.core.config import get_settings

class GeminiEmbeddingService(EmbeddingService):
    def __init__(self, model_name: str = "gemini-embedding-2", api_key: str | None = None):
        self.model_name = model_name
        settings = get_settings()
        self.client = genai.Client(api_key=api_key or settings.GOOGLE_API_KEY)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=texts,
        )
        embeddings = [e.values for e in response.embeddings]
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=[query],
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)

    def dimension(self) -> int:
        return 3072

    def _load_model(self):
        pass
