"""RAG Engine — orchestrates the full query→answer pipeline via multi-agent system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.gateway import AIGateway
from app.services.embeddings.embedding_service import EmbeddingService
from app.services.embeddings.vector_store import FAISSVectorStore
from app.services.rag.context_builder import build_context, extract_sources, build_repo_summary
from app.services.rag.query_classifier import classify_query
from app.services.rag.retriever import RAGRetriever


@dataclass
class Source:
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None


@dataclass
class RAGResponse:
    answer: str
    sources: list[Source]
    query_category: str
    model_used: str


class RAGEngine:
    """Orchestrates the full RAG pipeline: classify → embed → retrieve → build → generate.

    In Phase 6, delegates to the multi-agent Orchestrator for intelligent routing.
    Falls back to the original pipeline if the Orchestrator is unavailable.
    """

    def __init__(
        self,
        ai_gateway: AIGateway,
        embedding_service: EmbeddingService,
        vector_store: FAISSVectorStore,
        settings,
    ):
        self.ai_gateway = ai_gateway
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.settings = settings
        self.retriever = RAGRetriever(embedding_service, vector_store)

    async def query(
        self,
        question: str,
        repo_stats: dict,
        byok_key: str | None = None,
        repo_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> RAGResponse:
        """Run the full RAG pipeline and return a grounded response.

        If repo_id and db are provided, uses the multi-agent Orchestrator.
        Otherwise falls back to the original direct pipeline.
        """
        # Phase 6: Try multi-agent orchestrator
        if repo_id is not None and db is not None:
            try:
                return await self._query_via_orchestrator(
                    question, repo_stats, byok_key, repo_id, db
                )
            except Exception:
                pass  # Fall back to direct pipeline

        # Fallback: original direct pipeline
        return await self._query_direct(question, repo_stats, byok_key)

    async def _query_via_orchestrator(
        self,
        question: str,
        repo_stats: dict,
        byok_key: str | None,
        repo_id: uuid.UUID,
        db: AsyncSession,
    ) -> RAGResponse:
        """Route query through the multi-agent Orchestrator."""
        from app.services.agents.orchestrator import Orchestrator

        orchestrator = Orchestrator()
        result = await orchestrator.process(
            query=question,
            repo_id=repo_id,
            db=db,
            ai_gateway=self.ai_gateway,
            retriever=self.retriever,
            repo_stats=repo_stats,
            byok_key=byok_key,
        )

        sources = [
            Source(
                file_path=s.file_path,
                start_line=s.start_line,
                end_line=s.end_line,
                symbol_name=s.symbol_name,
            )
            for s in result.sources
        ]

        model_used = "deterministic" if not result.used_llm else self.settings.AI_MODEL

        return RAGResponse(
            answer=result.answer,
            sources=sources,
            query_category=result.query_category,
            model_used=model_used,
        )

    async def _query_direct(
        self,
        question: str,
        repo_stats: dict,
        byok_key: str | None = None,
    ) -> RAGResponse:
        """Original Phase 3 direct pipeline (fallback)."""
        # 1. Classify
        category = classify_query(question)

        # 2 & 3. Retrieve
        contexts = await self.retriever.retrieve(
            query=question,
            category=category,
            top_k=self.settings.VECTOR_SEARCH_TOP_K,
        )

        # 4. Build prompt
        repo_summary = build_repo_summary(repo_stats)
        system_prompt, user_prompt = build_context(question, contexts, repo_summary)

        # 5. Generate
        answer, model_used = await self.ai_gateway.generate(
            prompt=user_prompt,
            system=system_prompt,
            byok_key=byok_key,
        )

        # 6. Extract sources
        source_dicts = extract_sources(contexts)
        sources = [
            Source(
                file_path=s["file_path"],
                start_line=s["start_line"],
                end_line=s["end_line"],
                symbol_name=s.get("symbol_name"),
            )
            for s in source_dicts
        ]

        return RAGResponse(
            answer=answer,
            sources=sources,
            query_category=category,
            model_used=model_used,
        )

    async def query_stream(
        self,
        question: str,
        repo_stats: dict,
        byok_key: str | None = None,
        repo_id: uuid.UUID | None = None,
        db: AsyncSession | None = None,
    ) -> tuple[AsyncIterator[str], str, list[Source]]:
        """Run RAG pipeline with streaming response.

        For multi-agent queries, falls back to the direct pipeline for streaming
        since multi-agent results are assembled, not streamed.

        Returns (text_stream, query_category, sources).
        """
        # For streaming, check if deterministic first
        if repo_id is not None and db is not None:
            try:
                from app.services.agents.orchestrator import Orchestrator
                orchestrator = Orchestrator()
                det = await orchestrator._try_deterministic(question.lower().strip(), repo_id, db)
                if det:
                    # Yield deterministic answer as a single chunk
                    async def det_stream():
                        yield det.answer
                    return det_stream(), det.query_category, [
                        Source(file_path=s.file_path, start_line=s.start_line, end_line=s.end_line, symbol_name=s.symbol_name)
                        for s in det.sources
                    ]
            except Exception:
                pass

        # Fall back to streaming pipeline
        category = classify_query(question)

        contexts = await self.retriever.retrieve(
            query=question,
            category=category,
            top_k=self.settings.VECTOR_SEARCH_TOP_K,
        )

        repo_summary = build_repo_summary(repo_stats)
        system_prompt, user_prompt = build_context(question, contexts, repo_summary)

        stream, model_used = await self.ai_gateway.generate_stream(
            prompt=user_prompt,
            system=system_prompt,
            byok_key=byok_key,
        )

        source_dicts = extract_sources(contexts)
        sources = [
            Source(
                file_path=s["file_path"],
                start_line=s["start_line"],
                end_line=s["end_line"],
                symbol_name=s.get("symbol_name"),
            )
            for s in source_dicts
        ]

        return stream, category, sources
