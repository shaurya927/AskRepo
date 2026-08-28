"""Code Analyst — code questions, function/class explanations, RAG-based investigation."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base import BaseAgent, AgentResult, Source


class CodeAgent(BaseAgent):
    """Answers questions about specific code: functions, classes, methods, and implementations."""

    name = "code_analyst"
    description = "Code questions, function explanations, class explanations, RAG-based investigation"

    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        retriever = kwargs.get("retriever")
        ai_gateway = kwargs.get("ai_gateway")
        repo_stats = kwargs.get("repo_stats", {})

        if not retriever:
            return AgentResult(
                agent_name=self.name,
                answer="Code search index not available.",
                confidence=0.2,
            )

        # Retrieve code-focused contexts
        contexts = retriever.retrieve(query=query, category="code", top_k=10)
        if not contexts:
            return AgentResult(
                agent_name=self.name,
                answer="No relevant code found for this query.",
                confidence=0.3,
            )

        sources = [
            Source(
                file_path=c.file_path,
                start_line=c.start_line,
                end_line=c.end_line,
                symbol_name=c.symbol_name,
            )
            for c in contexts
        ]

        # Build context text
        context_text = "\n\n".join(
            f"=== {c.file_path}:{c.start_line}-{c.end_line} [{c.symbol_type}: {c.symbol_name}] ===\n{c.text}"
            if c.symbol_name
            else f"=== {c.file_path}:{c.start_line}-{c.end_line} ===\n{c.text}"
            for c in contexts
        )

        if ai_gateway:
            from app.services.rag.context_builder import build_repo_summary
            repo_summary = build_repo_summary(repo_stats)

            system = (
                "You are AskRepo's Code Analyst. You are an expert at reading and explaining source code. "
                "Rules:\n"
                "1. ONLY use information from the provided source context. Never invent file names or line numbers.\n"
                "2. Cite sources as `file_path:start_line-end_line`.\n"
                "3. Include relevant code snippets in your answer.\n"
                "4. Be precise and technical — developers are your audience.\n"
                "5. If the context doesn't contain enough information, say so clearly."
            )
            user_prompt = (
                f"Repository: {repo_summary}\n\n"
                f"Source code:\n{context_text}\n\n"
                f"Question: {query}\n\nProvide a detailed, code-grounded answer."
            )

            try:
                answer, _ = await ai_gateway.generate(
                    prompt=user_prompt, system=system, byok_key=kwargs.get("byok_key")
                )
                return AgentResult(
                    agent_name=self.name,
                    answer=answer,
                    sources=sources,
                    confidence=0.9,
                    used_llm=True,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"CodeAgent LLM failed (likely rate limit): {e}")

        # Fallback: return raw contexts
        return AgentResult(
            agent_name=self.name,
            answer=f"⚠️ **AI Generation Failed** (likely due to API rate limits). Here are the raw code sections I found instead:\n\n{context_text[:3000]}",
            sources=sources,
            confidence=0.6,
            used_llm=False,
        )
