"""RAG Retriever — multi-strategy retrieval based on query category."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.embeddings.embedding_service import EmbeddingService
from app.services.embeddings.vector_store import FAISSVectorStore, SearchResult


@dataclass
class RetrievedContext:
    """A retrieved chunk of context for the LLM."""
    text: str
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None
    symbol_type: str | None
    language: str | None
    relevance_score: float


class RAGRetriever:
    """Multi-strategy retriever that adapts to query category."""

    def __init__(self, embedding_service: EmbeddingService, vector_store: FAISSVectorStore):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        category: str,
        top_k: int = 15,
    ) -> list[RetrievedContext]:
        """Retrieve relevant contexts using category-specific strategy (async to prevent blocking)."""
        import asyncio
        
        def _blocking_retrieve():
            query_embedding = self.embedding_service.embed_query(query)
            return self.vector_store.search(query_embedding, top_k=self._get_top_k(category, top_k))
            
        results = await asyncio.to_thread(_blocking_retrieve)

        # Apply category-specific filtering/reranking
        if category == "code":
            results = self._filter_code(results)
        elif category == "architecture":
            results = self._filter_architecture(results)
        elif category == "repository":
            results = self._boost_documentation(results)

        return [self._to_context(r) for r in results]

    def _get_top_k(self, category: str, default: int) -> int:
        """Adjust top_k based on category."""
        overrides = {
            "code": min(default, 10),
            "architecture": min(default, 12),
            "repository": min(default, 8),
        }
        return overrides.get(category, default)

    def _filter_code(self, results: list[SearchResult]) -> list[SearchResult]:
        """For code questions, prioritize functions/methods over docs."""
        code_types = {"function", "method", "class", "interface"}
        code_results = [r for r in results if r.metadata.get("symbol_type") in code_types]
        other = [r for r in results if r not in code_results]
        # Return code results first, then fill with others
        return (code_results + other)[: len(results)]

    def _filter_architecture(self, results: list[SearchResult]) -> list[SearchResult]:
        """For architecture questions, include docs and important code."""
        # Boost files in typical architectural paths
        arch_keywords = {"service", "controller", "route", "api", "model", "config", "main", "app"}

        def arch_score(r: SearchResult) -> float:
            fp = r.metadata.get("file_path", "").lower()
            bonus = sum(0.1 for kw in arch_keywords if kw in fp)
            return r.score + bonus

        return sorted(results, key=arch_score, reverse=True)

    def _boost_documentation(self, results: list[SearchResult]) -> list[SearchResult]:
        """For repository questions, prioritize documentation and config."""
        doc_types = {"documentation", "config"}

        def doc_score(r: SearchResult) -> float:
            if r.metadata.get("chunk_type") in doc_types:
                return r.score + 0.5
            return r.score

        return sorted(results, key=doc_score, reverse=True)

    def _to_context(self, result: SearchResult) -> RetrievedContext:
        meta = result.metadata
        return RetrievedContext(
            text=result.text,
            file_path=meta.get("file_path", ""),
            start_line=meta.get("start_line", 0),
            end_line=meta.get("end_line", 0),
            symbol_name=meta.get("symbol_name"),
            symbol_type=meta.get("symbol_type"),
            language=meta.get("language"),
            relevance_score=result.score,
        )
