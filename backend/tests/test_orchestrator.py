"""Tests for the multi-agent orchestrator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.agents.orchestrator import Orchestrator
from app.services.agents.base import AgentResult, Source


class TestQueryRouting:
    """Test that queries are routed to the correct agents."""

    def setup_method(self):
        self.orchestrator = Orchestrator()

    def test_code_query_routes_to_code_agent(self):
        agents = self.orchestrator._route_query("what does the login function do", "code")
        assert "code_analyst" in agents

    def test_architecture_query_routes_to_arch_agent(self):
        agents = self.orchestrator._route_query("how is the project structured", "architecture")
        assert "architecture_analyst" in agents

    def test_history_query_routes_to_git_agent(self):
        agents = self.orchestrator._route_query("when did authentication change", "historical")
        assert "git_historian" in agents

    def test_repository_query_routes_to_repo_agent(self):
        agents = self.orchestrator._route_query("what is this project about", "repository")
        assert "repository_analyst" in agents

    def test_general_query_routes_to_code_agent(self):
        agents = self.orchestrator._route_query("hello", "general")
        assert "code_analyst" in agents

    def test_why_query_triggers_multi_agent(self):
        """'Why' questions should trigger code + git historian."""
        agents = self.orchestrator._route_query("why does authentication work this way", "code")
        assert "code_analyst" in agents
        assert "git_historian" in agents

    def test_refactor_triggers_quality_agent(self):
        agents = self.orchestrator._route_query("what should I refactor", "general")
        assert "quality_analyst" in agents

    def test_complexity_triggers_quality_agent(self):
        agents = self.orchestrator._route_query("what is the most complex function", "code")
        assert "quality_analyst" in agents

    def test_max_three_agents(self):
        """Should cap at 3 agents maximum."""
        agents = self.orchestrator._route_query(
            "why does the complex authentication refactor work this way and how did it evolve",
            "code"
        )
        assert len(agents) <= 3


class TestDeterministicPatterns:
    """Test that deterministic queries are correctly identified."""

    def test_file_count_pattern(self):
        import re
        from app.services.agents.orchestrator import _DETERMINISTIC_PATTERNS
        # Test all file_count patterns
        file_count_patterns = [p[0] for p in _DETERMINISTIC_PATTERNS if p[1] == "file_count"]

        assert any(re.search(p, "how many python files", re.IGNORECASE) for p in file_count_patterns)
        assert any(re.search(p, "total files in the repo", re.IGNORECASE) for p in file_count_patterns)

    def test_complexity_pattern(self):
        import re
        from app.services.agents.orchestrator import _DETERMINISTIC_PATTERNS
        complexity_patterns = [p[0] for p in _DETERMINISTIC_PATTERNS if p[1] == "complexity_rank"]

        assert any(re.search(p, "most complex function", re.IGNORECASE) for p in complexity_patterns)
        assert any(re.search(p, "highest complexity score", re.IGNORECASE) for p in complexity_patterns)

    def test_hotspot_pattern(self):
        import re
        from app.services.agents.orchestrator import _DETERMINISTIC_PATTERNS
        hotspot_patterns = [p[0] for p in _DETERMINISTIC_PATTERNS if p[1] == "hotspot_rank"]

        assert any(re.search(p, "most changed file in the project", re.IGNORECASE) for p in hotspot_patterns)
        assert any(re.search(p, "most frequently changed files", re.IGNORECASE) for p in hotspot_patterns)


class TestSynthesisAgent:
    """Test the synthesis agent."""

    @pytest.mark.asyncio
    async def test_single_result_passthrough(self):
        from app.services.agents.synthesis_agent import SynthesisAgent
        synth = SynthesisAgent()

        result = AgentResult(agent_name="test", answer="Hello", confidence=0.9)
        merged = await synth.synthesize("question", [result])
        assert merged.answer == "Hello"
        assert merged.agent_name == "test"

    @pytest.mark.asyncio
    async def test_multiple_results_merged(self):
        from app.services.agents.synthesis_agent import SynthesisAgent
        synth = SynthesisAgent()

        r1 = AgentResult(agent_name="agent_a", answer="Answer A", confidence=0.8)
        r2 = AgentResult(agent_name="agent_b", answer="Answer B", confidence=0.7)
        merged = await synth.synthesize("question", [r1, r2])
        # Without AI gateway, should concatenate
        assert "Agent A" in merged.answer or "agent_a" in merged.answer
        assert "Agent B" in merged.answer or "agent_b" in merged.answer

    @pytest.mark.asyncio
    async def test_sources_deduplicated(self):
        from app.services.agents.synthesis_agent import SynthesisAgent
        synth = SynthesisAgent()

        s = Source(file_path="a.py", start_line=1, end_line=10)
        r1 = AgentResult(agent_name="a", answer="A", sources=[s], confidence=0.8)
        r2 = AgentResult(agent_name="b", answer="B", sources=[s], confidence=0.7)
        merged = await synth.synthesize("q", [r1, r2])
        assert len(merged.sources) == 1

    @pytest.mark.asyncio
    async def test_empty_results(self):
        from app.services.agents.synthesis_agent import SynthesisAgent
        synth = SynthesisAgent()
        merged = await synth.synthesize("q", [])
        assert merged.confidence == 0.0
