"""Git Historian — commit history, code evolution, historical reasoning."""

from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commit import Commit
from app.models.file_change import FileChange
from app.services.agents.base import BaseAgent, AgentResult, Source


class GitAgent(BaseAgent):
    """Answers questions about commit history, code evolution, and historical reasoning."""

    name = "git_historian"
    description = "Commit history, code evolution, historical reasoning"

    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        # Check if we have any commit data
        count_result = await db.execute(
            select(func.count()).select_from(Commit).where(Commit.repository_id == repo_id)
        )
        commit_count = count_result.scalar() or 0

        if commit_count == 0:
            return AgentResult(
                agent_name=self.name,
                answer="No git history available for this repository. Git history is only available for GitHub-cloned repositories.",
                confidence=0.3,
                used_llm=False,
            )

        # Gather relevant history data based on query
        q = query.lower()

        # Search for commits by message keywords
        keywords = [w for w in q.split() if len(w) > 3 and w not in {"this", "that", "what", "when", "which", "does", "have", "been"}]
        relevant_commits = []

        if keywords:
            for keyword in keywords[:5]:
                result = await db.execute(
                    select(Commit)
                    .where(Commit.repository_id == repo_id, Commit.message.ilike(f"%{keyword}%"))
                    .order_by(Commit.authored_date.desc())
                    .limit(10)
                )
                for c in result.scalars().all():
                    if c.sha not in [rc.sha for rc in relevant_commits]:
                        relevant_commits.append(c)

        # Also get recent commits for general history context
        recent_result = await db.execute(
            select(Commit)
            .where(Commit.repository_id == repo_id)
            .order_by(Commit.authored_date.desc())
            .limit(20)
        )
        recent_commits = recent_result.scalars().all()

        # Get file changes for relevant commits
        relevant_shas = list({c.sha for c in relevant_commits})[:20]
        file_changes = []
        if relevant_shas:
            fc_result = await db.execute(
                select(FileChange).where(
                    FileChange.repository_id == repo_id,
                    FileChange.commit_sha.in_(relevant_shas),
                )
            )
            file_changes = fc_result.scalars().all()

        # Get hotspot data
        from app.services.git.git_analyzer import GitAnalyzer
        all_fc_result = await db.execute(
            select(FileChange).where(FileChange.repository_id == repo_id)
        )
        all_file_changes = [
            {"file_path": fc.file_path, "insertions": fc.insertions, "deletions": fc.deletions, "commit_sha": fc.commit_sha}
            for fc in all_fc_result.scalars().all()
        ]
        hotspots = GitAnalyzer.get_change_frequency(all_file_changes)[:10]

        # Build history context
        parts = [f"**Git History Summary**: {commit_count} total commits analyzed\n"]

        if relevant_commits:
            parts.append("**Relevant commits (matching query keywords):**")
            for c in relevant_commits[:10]:
                date_str = c.authored_date.strftime("%Y-%m-%d")
                parts.append(f"- `{c.sha[:7]}` ({date_str}) by {c.author_name}: {c.message[:200]}")
                # Add file changes for this commit
                commit_fcs = [fc for fc in file_changes if fc.commit_sha == c.sha]
                if commit_fcs:
                    for fc in commit_fcs[:5]:
                        parts.append(f"  - [{fc.change_type}] {fc.file_path} (+{fc.insertions}/-{fc.deletions})")

        parts.append("\n**Recent commits:**")
        for c in recent_commits[:10]:
            date_str = c.authored_date.strftime("%Y-%m-%d")
            parts.append(f"- `{c.sha[:7]}` ({date_str}) by {c.author_name}: {c.message[:150]}")

        if hotspots:
            parts.append("\n**Most frequently changed files (hotspots):**")
            for h in hotspots[:5]:
                parts.append(f"- {h['file_path']}: changed {h['change_count']} times (+{h['total_insertions']}/-{h['total_deletions']})")

        history_context = "\n".join(parts)

        # For simple deterministic queries
        if any(kw in q for kw in ["most changed", "hotspot", "frequently", "how often"]):
            return AgentResult(
                agent_name=self.name,
                answer=history_context,
                confidence=0.9,
                used_llm=False,
            )

        # Use LLM for interpretive historical questions
        ai_gateway = kwargs.get("ai_gateway")
        if ai_gateway:
            system = (
                "You are AskRepo's Git Historian. You answer questions about code evolution "
                "and historical changes based on actual git commit data.\n"
                "Rules:\n"
                "1. ONLY use the provided commit history data. NEVER fabricate commits, dates, or authors.\n"
                "2. Cite specific commit SHAs when referencing changes.\n"
                "3. If the history data doesn't contain enough information, say so clearly.\n"
                "4. Focus on the 'why' behind changes when commit messages provide that context."
            )
            user_prompt = (
                f"Git history data:\n\n{history_context}\n\n"
                f"Question: {query}\n\nProvide a historically-grounded answer."
            )
            try:
                answer, _ = await ai_gateway.generate(
                    prompt=user_prompt, system=system, byok_key=kwargs.get("byok_key")
                )
                return AgentResult(
                    agent_name=self.name,
                    answer=answer,
                    confidence=0.85,
                    used_llm=True,
                )
            except Exception:
                pass

        return AgentResult(
            agent_name=self.name,
            answer=history_context,
            confidence=0.7,
            used_llm=False,
        )
