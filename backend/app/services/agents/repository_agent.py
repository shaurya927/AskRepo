"""Repository Analyst — project overview, tech stack, major modules, entry points."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository import Repository
from app.models.repository_stats import RepositoryStats
from app.models.repository_file import RepositoryFile
from app.services.agents.base import BaseAgent, AgentResult, Source


class RepositoryAgent(BaseAgent):
    """Answers questions about the repository's overview, tech stack, and structure."""

    name = "repository_analyst"
    description = "Project overview, technology stack, major modules, entry points"

    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        # Gather deterministic data
        repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
        repo = repo_result.scalar_one_or_none()

        stats_result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
        stats = stats_result.scalar_one_or_none()

        if not stats:
            return AgentResult(agent_name=self.name, answer="No repository statistics available.", confidence=0.3)

        # Build a comprehensive summary from DB data
        parts = []
        parts.append(f"**Repository: {repo.name if repo else 'Unknown'}**\n")

        if stats.primary_language:
            parts.append(f"- **Primary Language:** {stats.primary_language}")
        parts.append(f"- **Total Files:** {stats.total_files}")
        parts.append(f"- **Total Lines:** {stats.total_lines:,}")
        parts.append(f"- **Total Size:** {stats.total_size:,} bytes")

        if stats.languages:
            lang_summary = ", ".join(
                f"{lang} ({info['files']} files, {info['lines']} lines)"
                for lang, info in sorted(stats.languages.items(), key=lambda x: x[1].get("lines", 0), reverse=True)[:5]
            )
            parts.append(f"- **Languages:** {lang_summary}")

        if stats.frameworks:
            parts.append(f"- **Frameworks:** {', '.join(stats.frameworks)}")
        if stats.package_managers:
            parts.append(f"- **Package Managers:** {', '.join(stats.package_managers)}")

        if stats.total_functions or stats.total_classes:
            parts.append(f"- **Functions:** {stats.total_functions or 0}, **Classes:** {stats.total_classes or 0}, **Methods:** {stats.total_methods or 0}")

        if stats.entry_points:
            parts.append(f"- **Entry Points:** {', '.join(stats.entry_points[:5])}")
        if stats.config_files:
            parts.append(f"- **Config Files:** {', '.join(stats.config_files[:5])}")
        if stats.test_files_count:
            parts.append(f"- **Test Files:** {stats.test_files_count}")

        # Check if we need LLM for a natural language answer
        ai_gateway = kwargs.get("ai_gateway")
        repo_stats = kwargs.get("repo_stats", {})
        q = query.lower()

        # For simple stat questions, return deterministic answer
        if any(kw in q for kw in ["how many", "count", "number of", "total"]):
            return AgentResult(
                agent_name=self.name,
                answer="\n".join(parts),
                confidence=0.95,
                used_llm=False,
            )

        # For overview/description questions, use LLM to produce a narrative
        if ai_gateway:
            system = (
                "You are AskRepo's Repository Analyst. Given repository statistics, "
                "produce a clear, concise overview of the project. Focus on what the project does, "
                "its tech stack, and its structure. Only use the provided data."
            )
            user_prompt = f"Repository data:\n\n{chr(10).join(parts)}\n\nUser question: {query}\n\nProvide a helpful answer."

            try:
                answer, model = await ai_gateway.generate(prompt=user_prompt, system=system, byok_key=kwargs.get("byok_key"))
                return AgentResult(agent_name=self.name, answer=answer, confidence=0.85, used_llm=True)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"RepositoryAgent LLM failed: {e}")
                parts.insert(0, "⚠️ **AI Generation Failed** (likely due to API rate limits). Here are the raw repository statistics:\n")

        return AgentResult(
            agent_name=self.name,
            answer="\n".join(parts),
            confidence=0.8,
            used_llm=False,
        )
