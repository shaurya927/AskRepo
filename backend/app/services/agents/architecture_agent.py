"""Architecture Analyst — architecture, dependencies, data flow, module relationships."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_symbol import CodeSymbol
from app.models.code_import import CodeImport
from app.services.agents.base import BaseAgent, AgentResult, Source


class ArchitectureAgent(BaseAgent):
    """Answers questions about architecture, dependencies, and module relationships."""

    name = "architecture_analyst"
    description = "Architecture, dependencies, data flow, module relationships"

    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        # Get architecture detection results
        from app.services.graph.architecture_detector import ArchitectureDetector
        from app.models.repository_file import RepositoryFile

        files_result = await db.execute(
            select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
        )
        files = [{"path": f.path, "language": f.language or ""} for f in files_result.scalars().all()]

        imports_result = await db.execute(
            select(CodeImport).where(CodeImport.repository_id == repo_id)
        )
        imports = [
            {"file_path": i.file_path, "source": i.source, "is_internal": i.is_internal}
            for i in imports_result.scalars().all()
        ]

        detector = ArchitectureDetector()
        detection = detector.detect(files, imports=imports)
        summary = detector.get_architecture_summary(detection)

        # Build deterministic architecture context
        parts = ["**Architecture Overview**\n"]
        for cat in summary.get("categories", []):
            parts.append(f"- **{cat['name'].capitalize()}**: {cat['file_count']} files ({cat['percentage']}%)")
            sample = detection.get(cat["name"], [])[:3]
            if sample:
                parts.append(f"  - e.g., {', '.join(sample)}")

        # Get module-level dependency info
        from app.services.graph.graph_builder import GraphBuilder
        symbols_result = await db.execute(
            select(CodeSymbol).where(CodeSymbol.repository_id == repo_id)
        )
        symbols = [
            {"file_path": s.file_path, "name": s.name, "symbol_type": s.symbol_type, "language": s.language}
            for s in symbols_result.scalars().all()
        ]
        imports_for_graph = [
            {"file_path": i.file_path, "source": i.source, "resolved_path": i.resolved_path, "is_internal": i.is_internal}
            for i in (await db.execute(select(CodeImport).where(CodeImport.repository_id == repo_id))).scalars().all()
        ]

        builder = GraphBuilder()
        file_graph = builder.build_file_graph(symbols, imports_for_graph)
        mod_graph = builder.build_module_graph(file_graph)

        if mod_graph.number_of_nodes() > 0:
            parts.append(f"\n**Module Structure**: {mod_graph.number_of_nodes()} modules, {mod_graph.number_of_edges()} dependencies")

        arch_context = "\n".join(parts)

        # Use LLM to explain architecture in context of the question
        ai_gateway = kwargs.get("ai_gateway")
        retriever = kwargs.get("retriever")

        # Also get RAG contexts for architecture-related code
        rag_context = ""
        sources = []
        if retriever:
            contexts = await retriever.retrieve(query=query, category="architecture", top_k=8)
            rag_context = "\n\n".join(
                f"=== {c.file_path} (lines {c.start_line}-{c.end_line}) ===\n{c.text}"
                for c in contexts
            )
            sources = [
                Source(file_path=c.file_path, start_line=c.start_line, end_line=c.end_line, symbol_name=c.symbol_name)
                for c in contexts
            ]

        if ai_gateway:
            system = (
                "You are AskRepo's Architecture Analyst. Explain the repository's architecture, "
                "component relationships, and data flow. Ground your answer in the provided "
                "architecture detection data and source code. Cite specific files."
            )
            user_prompt = (
                f"Architecture analysis:\n{arch_context}\n\n"
                f"Relevant source code:\n{rag_context}\n\n"
                f"Question: {query}\n\nProvide a detailed architectural analysis."
            )
            try:
                answer, _ = await ai_gateway.generate(prompt=user_prompt, system=system, byok_key=kwargs.get("byok_key"))
                return AgentResult(agent_name=self.name, answer=answer, sources=sources, confidence=0.85, used_llm=True)
            except Exception:
                pass

        return AgentResult(agent_name=self.name, answer=arch_context, sources=sources, confidence=0.7, used_llm=False)
