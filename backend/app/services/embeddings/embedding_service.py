"""Embedding service — abstracts text-to-vector conversion."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class EmbeddingService(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> np.ndarray:
        ...

    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        ...

    @abstractmethod
    def dimension(self) -> int:
        ...


# Singleton to avoid reloading the model on every call
_st_instance: "SentenceTransformerEmbedding | None" = None


class SentenceTransformerEmbedding(EmbeddingService):
    """Embedding implementation using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
        self.model_name = model_name
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        model = self._load_model()
        embedding = model.encode(
            [query],
            normalize_embeddings=True,
        )
        return np.array(embedding, dtype=np.float32)[0]

    def dimension(self) -> int:
        model = self._load_model()
        return model.get_sentence_embedding_dimension()


def get_embedding_service(
    model_name: str = "gemini-embedding-2",
    batch_size: int = 64,
) -> EmbeddingService:
    """Return a singleton embedding service instance."""
    global _st_instance
    
    if "gemini" in model_name:
        if _st_instance is None or getattr(_st_instance, "model_name", None) != model_name:
            from app.services.embeddings.gemini_embedding import GeminiEmbeddingService
            _st_instance = GeminiEmbeddingService(model_name)
        return _st_instance
        
    if _st_instance is None or getattr(_st_instance, "model_name", None) != model_name:
        _st_instance = SentenceTransformerEmbedding(model_name, batch_size)
    return _st_instance
