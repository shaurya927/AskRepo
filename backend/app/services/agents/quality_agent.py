"""Quality Analyst — complexity, coupling, missing tests, suspicious patterns."""

from __future__ import annotations

import uuid

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_symbol import CodeSymbol
from app.models.repository_stats import RepositoryStats
from app.models.repository_file import RepositoryFile
from app.services.agents.base import BaseAgent, AgentResult, Source


class QualityAgent(BaseAgent):
    """Answers questions about code quality, complexity, and potential improvements."""

    name = "quality_analyst"
    description = "Complexity, coupling, missing tests, suspicious patterns, static analysis findings"

    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        q = query.lower()

        # Get complexity data
        complex_result = await db.execute(
            select(CodeSymbol)
            .where(CodeSymbol.repository_id == repo_id, CodeSymbol.complexity.isnot(None))
            .order_by(desc(CodeSymbol.complexity))
            .limit(20)
        )
        complex_symbols = complex_result.scalars().all()

        # Get stats
        stats_result = await db.execute(
            select(RepositoryStats).where(RepositoryStats.repository_id == repo_id)
        )
        stats = stats_result.scalar_one_or_none()

        # Get file count for test coverage estimation
        total_files_result = await db.execute(
            select(func.count()).select_from(RepositoryFile).where(
                RepositoryFile.repository_id == repo_id
            )
        )
        total_files = total_files_result.scalar() or 0

        # Build quality report
        parts = ["**Code Quality Analysis**\n"]

        # Complexity
        if stats:
            parts.append(f"- **Average Complexity:** {stats.avg_complexity}")
            parts.append(f"- **Max Complexity:** {stats.max_complexity}")
            if stats.complexity_distribution:
                parts.append(f"- **Distribution:** {stats.complexity_distribution}")
            parts.append(f"- **Test Files:** {stats.test_files_count or 0}")

        if complex_symbols:
            parts.append("\n**Most Complex Functions/Methods:**")
            sources = []
            for s in complex_symbols[:10]:
                parts.append(
                    f"- `{s.name}` in `{s.file_path}` (complexity: {s.complexity}, "
                    f"lines {s.start_line}-{s.end_line})"
                )
                sources.append(Source(
                    file_path=s.file_path,
                    start_line=s.start_line or 0,
                    end_line=s.end_line or 0,
                    symbol_name=s.name,
                ))
        else:
            sources = []

        # Test coverage estimate
        test_count = stats.test_files_count if stats else 0
        source_files = total_files - test_count
        if source_files > 0 and test_count > 0:
            ratio = round(test_count / source_files * 100, 1)
            parts.append(f"\n**Test Coverage Estimate:** {test_count} test files / {source_files} source files ({ratio}% file-level coverage)")
        elif test_count == 0:
            parts.append("\n⚠️ **No test files detected** in this repository.")

        # Large files (potential code smells)
        large_result = await db.execute(
            select(RepositoryFile)
            .where(RepositoryFile.repository_id == repo_id)
            .order_by(desc(RepositoryFile.lines))
            .limit(5)
        )
        large_files = large_result.scalars().all()
        if large_files and large_files[0].lines and large_files[0].lines > 300:
            parts.append("\n**Largest Files (potential refactoring candidates):**")
            for f in large_files:
                if f.lines and f.lines > 200:
                    parts.append(f"- `{f.path}`: {f.lines} lines")

        quality_context = "\n".join(parts)

        # For deterministic queries
        if any(kw in q for kw in ["most complex", "highest complexity", "complexity", "how many test"]):
            return AgentResult(
                agent_name=self.name,
                answer=quality_context,
                sources=sources,
                confidence=0.95,
                used_llm=False,
            )

        # Use LLM for advisory questions
        ai_gateway = kwargs.get("ai_gateway")
        if ai_gateway:
            system = (
                "You are AskRepo's Quality Analyst. You identify code quality issues, "
                "suggest refactoring opportunities, and highlight potential problems.\n"
                "Rules:\n"
                "1. Base your analysis on the provided metrics and code data.\n"
                "2. Be specific about which files/functions need attention.\n"
                "3. Prioritize actionable suggestions.\n"
                "4. Cite specific complexity scores and line counts."
            )
            user_prompt = (
                f"Quality data:\n{quality_context}\n\n"
                f"Question: {query}\n\nProvide actionable quality analysis."
            )
            try:
                answer, _ = await ai_gateway.generate(
                    prompt=user_prompt, system=system, byok_key=kwargs.get("byok_key")
                )
                return AgentResult(
                    agent_name=self.name,
                    answer=answer,
                    sources=sources,
                    confidence=0.85,
                    used_llm=True,
                )
            except Exception:
                pass

        return AgentResult(
            agent_name=self.name,
            answer=quality_context,
            sources=sources,
            confidence=0.75,
            used_llm=False,
        )
