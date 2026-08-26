"""FAISS-based vector store for code search."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class SearchResult:
    """A single search result from the vector store."""
    chunk_id: str
    score: float
    text: str
    metadata: dict


class FAISSVectorStore:
    """Vector store backed by FAISS for similarity search."""

    def __init__(self):
        self._index = None
        self._texts: list[str] = []
        self._metadata: list[dict] = []
        self._chunk_ids: list[str] = []

    def build_index(
        self,
        embeddings: np.ndarray,
        texts: list[str],
        metadata: list[dict],
        chunk_ids: list[str],
    ):
        """Build a FAISS index from embeddings."""
        import faiss

        dim = embeddings.shape[1]
        # Use inner product (cosine sim on normalized vectors)
        self._index = faiss.IndexFlatIP(dim)
        self._index.add(embeddings)
        self._texts = texts
        self._metadata = metadata
        self._chunk_ids = chunk_ids

    def search(self, query_embedding: np.ndarray, top_k: int = 15) -> list[SearchResult]:
        """Search for the most similar chunks."""
        if self._index is None or self._index.ntotal == 0:
            return []

        query = query_embedding.reshape(1, -1).astype(np.float32)
        top_k = min(top_k, self._index.ntotal)
        scores, indices = self._index.search(query, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append(SearchResult(
                chunk_id=self._chunk_ids[idx],
                score=float(score),
                text=self._texts[idx],
                metadata=self._metadata[idx],
            ))
        return results

    def save(self, directory: Path):
        """Persist index and metadata to disk."""
        import faiss

        directory.mkdir(parents=True, exist_ok=True)
        if self._index is not None:
            faiss.write_index(self._index, str(directory / "index.faiss"))
        with open(directory / "metadata.json", "w", encoding="utf-8") as f:
            json.dump({
                "texts": self._texts,
                "metadata": self._metadata,
                "chunk_ids": self._chunk_ids,
            }, f)

    def load(self, directory: Path) -> bool:
        """Load index and metadata from disk. Returns True if successful."""
        import faiss

        index_path = directory / "index.faiss"
        meta_path = directory / "metadata.json"
        if not index_path.exists() or not meta_path.exists():
            return False
        try:
            self._index = faiss.read_index(str(index_path))
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._texts = data["texts"]
            self._metadata = data["metadata"]
            self._chunk_ids = data["chunk_ids"]
            return True
        except Exception:
            return False

    @property
    def size(self) -> int:
        return self._index.ntotal if self._index else 0
