"""Base agent interface and shared data structures."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class Source:
    """A source citation from an agent's analysis."""
    file_path: str
    start_line: int = 0
    end_line: int = 0
    symbol_name: str | None = None


@dataclass
class AgentResult:
    """Output from a single agent's analysis."""
    agent_name: str
    answer: str
    sources: list[Source] = field(default_factory=list)
    confidence: float = 1.0
    used_llm: bool = False


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    name: str = "base"
    description: str = "Base agent"

    @abstractmethod
    async def analyze(
        self,
        query: str,
        repo_id: uuid.UUID,
        db: AsyncSession,
        **kwargs,
    ) -> AgentResult:
        """Analyze a query and return a result.

        Args:
            query: The user's question.
            repo_id: The repository UUID.
            db: Async database session.
            **kwargs: Additional context (repo_stats, settings, ai_gateway, etc.)

        Returns:
            AgentResult with the agent's answer and sources.
        """
        ...
