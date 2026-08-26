"""Orchestrator — routes queries to the right agents and assembles responses."""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base import AgentResult, Source
from app.services.agents.repository_agent import RepositoryAgent
from app.services.agents.architecture_agent import ArchitectureAgent
from app.services.agents.code_agent import CodeAgent
from app.services.agents.git_agent import GitAgent
from app.services.agents.quality_agent import QualityAgent
from app.services.agents.synthesis_agent import SynthesisAgent
from app.services.rag.query_classifier import classify_query

logger = logging.getLogger(__name__)


# Deterministic query patterns that don't need an LLM
_DETERMINISTIC_PATTERNS = [
    (r"how many (\w+) files", "file_count"),
    (r"number of files", "file_count"),
    (r"total files", "file_count"),
    (r"most complex", "complexity_rank"),
    (r"highest complexity", "complexity_rank"),
    (r"most changed file", "hotspot_rank"),
    (r"most frequently changed", "hotspot_rank"),
    (r"what languages?", "languages"),
    (r"what framework", "frameworks"),
    (r"tech stack", "tech_stack"),
]

# Additional signals for multi-agent routing
_MULTI_AGENT_SIGNALS = {
    "why": ["code_analyst", "git_historian"],
    "how does.*work": ["architecture_analyst", "code_analyst"],
    "authentication": ["architecture_analyst", "code_analyst"],
    "refactor": ["quality_analyst", "code_analyst"],
    "improve": ["quality_analyst"],
    "test coverage": ["quality_analyst"],
    "evolve": ["git_historian", "architecture_analyst"],
    "change.*between": ["git_historian"],
}


@dataclass
class OrchestratorResult:
    """Result from the orchestrator."""
    answer: str
    sources: list[Source] = field(default_factory=list)
    query_category: str = "general"
    agents_used: list[str] = field(default_factory=list)
    used_llm: bool = False


class Orchestrator:
    """Routes queries to specialized agents and combines results."""

    def __init__(self):
        self.agents = {
            "repository_analyst": RepositoryAgent(),
            "architecture_analyst": ArchitectureAgent(),
            "code_analyst": CodeAgent(),
            "git_historian": GitAgent(),
            "quality_analyst": QualityAgent(),
        }
        self.synthesis = SynthesisAgent()

    async def process(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        ai_gateway=None,
        retriever=None,
        repo_stats: dict | None = None,
        byok_key: str | None = None,
    ) -> OrchestratorResult:
        """Process a query through the multi-agent system.

        1. Check for deterministic-only queries
        2. Classify and route to agents
        3. Run agents in parallel
        4. Synthesize if multiple agents
        """
        q = query.lower().strip()
        repo_stats = repo_stats or {}

        # Step 1: Check deterministic queries
        deterministic = await self._try_deterministic(q, repo_id, db)
        if deterministic:
            return deterministic

        # Step 2: Classify and determine which agents to use
        category = classify_query(query)
        agent_names = self._route_query(q, category)

        logger.info("Query classified as '%s', routing to agents: %s", category, agent_names)

        # Step 3: Run selected agents in parallel
        kwargs = {
            "ai_gateway": ai_gateway,
            "retriever": retriever,
            "repo_stats": repo_stats,
            "byok_key": byok_key,
        }

        tasks = []
        for name in agent_names:
            agent = self.agents.get(name)
            if agent:
                tasks.append(agent.analyze(query, repo_id, db, **kwargs))

        if not tasks:
            return OrchestratorResult(
                answer="I couldn't determine how to answer this question. Please try rephrasing.",
                query_category=category,
            )

        results: list[AgentResult] = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, AgentResult)]
        if not valid_results:
            return OrchestratorResult(
                answer="All agents failed to process the query. Please try again.",
                query_category=category,
                agents_used=agent_names,
            )

        # Step 4: Synthesize if multiple results
        if len(valid_results) > 1:
            final = await self.synthesis.synthesize(
                query=query,
                results=valid_results,
                ai_gateway=ai_gateway,
                byok_key=byok_key,
            )
        else:
            final = valid_results[0]

        return OrchestratorResult(
            answer=final.answer,
            sources=final.sources,
            query_category=f"{category}:{','.join(agent_names)}",
            agents_used=[r.agent_name for r in valid_results],
            used_llm=final.used_llm,
        )

    def _route_query(self, query: str, category: str) -> list[str]:
        """Determine which agents should handle this query."""
        # Primary routing by category
        primary_map = {
            "repository": ["repository_analyst"],
            "architecture": ["architecture_analyst"],
            "code": ["code_analyst"],
            "historical": ["git_historian"],
            "general": ["code_analyst"],
        }
        agents = list(primary_map.get(category, ["code_analyst"]))

        # Check for multi-agent signals
        for pattern, extra_agents in _MULTI_AGENT_SIGNALS.items():
            if re.search(pattern, query, re.IGNORECASE):
                for ea in extra_agents:
                    if ea not in agents:
                        agents.append(ea)

        # Quality-related keywords
        quality_kws = ["complexity", "complex", "refactor", "quality", "test coverage", "code smell", "coupling"]
        if any(kw in query for kw in quality_kws):
            if "quality_analyst" not in agents:
                agents.append("quality_analyst")

        return agents[:3]  # Cap at 3 agents max

    async def _try_deterministic(
        self, query: str, repo_id: uuid.UUID, db: AsyncSession
    ) -> OrchestratorResult | None:
        """Try to answer with deterministic DB queries (no LLM)."""

        for pattern, query_type in _DETERMINISTIC_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if not match:
                continue

            if query_type == "file_count":
                return await self._answer_file_count(query, repo_id, db, match)
            elif query_type == "complexity_rank":
                return await self._answer_complexity_rank(repo_id, db)
            elif query_type == "hotspot_rank":
                return await self._answer_hotspot_rank(repo_id, db)
            elif query_type == "languages":
                return await self._answer_languages(repo_id, db)
            elif query_type in ("frameworks", "tech_stack"):
                return await self._answer_tech_stack(repo_id, db)

        return None

    async def _answer_file_count(
        self, query: str, repo_id: uuid.UUID, db: AsyncSession, match
    ) -> OrchestratorResult:
        from app.models.repository_file import RepositoryFile
        from app.models.repository_stats import RepositoryStats

        # Check if asking about a specific language
        lang_word = match.group(1) if match.lastindex else None
        lang_map = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
            "java": "Java", "cpp": "C++", "go": "Go", "rust": "Rust", "ruby": "Ruby",
        }

        if lang_word and lang_word.lower() in lang_map:
            lang = lang_map[lang_word.lower()]
            count_result = await db.execute(
                select(func.count()).select_from(RepositoryFile).where(
                    RepositoryFile.repository_id == repo_id,
                    RepositoryFile.language == lang,
                )
            )
            count = count_result.scalar() or 0
            return OrchestratorResult(
                answer=f"There are **{count}** {lang} files in this repository.",
                query_category="deterministic:file_count",
                agents_used=["deterministic"],
            )

        # Total files
        stats_result = await db.execute(
            select(RepositoryStats).where(RepositoryStats.repository_id == repo_id)
        )
        stats = stats_result.scalar_one_or_none()
        total = stats.total_files if stats else 0
        return OrchestratorResult(
            answer=f"There are **{total}** files in this repository.",
            query_category="deterministic:file_count",
            agents_used=["deterministic"],
        )

    async def _answer_complexity_rank(
        self, repo_id: uuid.UUID, db: AsyncSession
    ) -> OrchestratorResult:
        from app.models.code_symbol import CodeSymbol
        result = await db.execute(
            select(CodeSymbol)
            .where(CodeSymbol.repository_id == repo_id, CodeSymbol.complexity.isnot(None))
            .order_by(desc(CodeSymbol.complexity))
            .limit(10)
        )
        symbols = result.scalars().all()

        if not symbols:
            return OrchestratorResult(
                answer="No complexity data available.",
                query_category="deterministic:complexity",
                agents_used=["deterministic"],
            )

        lines = ["**Most Complex Functions/Methods:**\n"]
        sources = []
        for i, s in enumerate(symbols, 1):
            lines.append(f"{i}. `{s.name}` in `{s.file_path}` — complexity: **{s.complexity}** (lines {s.start_line}-{s.end_line})")
            sources.append(Source(file_path=s.file_path, start_line=s.start_line or 0, end_line=s.end_line or 0, symbol_name=s.name))

        return OrchestratorResult(
            answer="\n".join(lines),
            sources=sources,
            query_category="deterministic:complexity",
            agents_used=["deterministic"],
        )

    async def _answer_hotspot_rank(
        self, repo_id: uuid.UUID, db: AsyncSession
    ) -> OrchestratorResult:
        from app.models.file_change import FileChange
        from app.services.git.git_analyzer import GitAnalyzer

        result = await db.execute(
            select(FileChange).where(FileChange.repository_id == repo_id)
        )
        fcs = [{"file_path": fc.file_path, "insertions": fc.insertions, "deletions": fc.deletions}
               for fc in result.scalars().all()]

        if not fcs:
            return OrchestratorResult(
                answer="No git history available to determine file change frequency.",
                query_category="deterministic:hotspot",
                agents_used=["deterministic"],
            )

        hotspots = GitAnalyzer.get_change_frequency(fcs)
        lines = ["**Most Frequently Changed Files:**\n"]
        for i, h in enumerate(hotspots[:10], 1):
            lines.append(f"{i}. `{h['file_path']}` — changed **{h['change_count']}** times (+{h['total_insertions']}/-{h['total_deletions']})")

        return OrchestratorResult(
            answer="\n".join(lines),
            query_category="deterministic:hotspot",
            agents_used=["deterministic"],
        )

    async def _answer_languages(
        self, repo_id: uuid.UUID, db: AsyncSession
    ) -> OrchestratorResult:
        from app.models.repository_stats import RepositoryStats
        result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
        stats = result.scalar_one_or_none()

        if not stats or not stats.languages:
            return OrchestratorResult(answer="No language data available.", query_category="deterministic:languages", agents_used=["deterministic"])

        lines = ["**Languages used in this repository:**\n"]
        for lang, info in sorted(stats.languages.items(), key=lambda x: x[1].get("lines", 0), reverse=True):
            lines.append(f"- **{lang}**: {info.get('files', 0)} files, {info.get('lines', 0):,} lines")

        return OrchestratorResult(answer="\n".join(lines), query_category="deterministic:languages", agents_used=["deterministic"])

    async def _answer_tech_stack(
        self, repo_id: uuid.UUID, db: AsyncSession
    ) -> OrchestratorResult:
        from app.models.repository_stats import RepositoryStats
        result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
        stats = result.scalar_one_or_none()

        if not stats:
            return OrchestratorResult(answer="No stats available.", query_category="deterministic:tech_stack", agents_used=["deterministic"])

        parts = []
        if stats.primary_language:
            parts.append(f"**Primary Language:** {stats.primary_language}")
        if stats.frameworks:
            parts.append(f"**Frameworks:** {', '.join(stats.frameworks)}")
        if stats.package_managers:
            parts.append(f"**Package Managers:** {', '.join(stats.package_managers)}")
        if stats.languages:
            langs = sorted(stats.languages.keys())
            parts.append(f"**All Languages:** {', '.join(langs)}")

        return OrchestratorResult(
            answer="\n".join(parts) if parts else "No tech stack information available.",
            query_category="deterministic:tech_stack",
            agents_used=["deterministic"],
        )
