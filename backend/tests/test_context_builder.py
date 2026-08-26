"""Tests for context builder."""

from app.services.rag.context_builder import (
    build_context, extract_sources, build_repo_summary, SYSTEM_PROMPT,
)
from app.services.rag.retriever import RetrievedContext


class TestBuildContext:

    def _make_ctx(self, file_path="app.py", start=1, end=10, name="func", text="code here"):
        return RetrievedContext(
            text=text, file_path=file_path, start_line=start, end_line=end,
            symbol_name=name, symbol_type="function", language="Python",
            relevance_score=0.9,
        )

    def test_includes_system_prompt(self):
        system, user = build_context("what?", [], "summary")
        assert system == SYSTEM_PROMPT

    def test_includes_repo_summary(self):
        _, user = build_context("what?", [], "My Repo Summary")
        assert "My Repo Summary" in user

    def test_includes_context(self):
        ctx = self._make_ctx(text="def hello(): return 1")
        _, user = build_context("what does hello do?", [ctx], "")
        assert "def hello(): return 1" in user

    def test_includes_source_location(self):
        ctx = self._make_ctx(file_path="src/main.py", start=5, end=15, name="main")
        _, user = build_context("q", [ctx], "")
        assert "src/main.py" in user
        assert "lines 5-15" in user

    def test_truncates_to_max_chars(self):
        contexts = [self._make_ctx(text="x" * 2000) for _ in range(20)]
        _, user = build_context("q", contexts, "", max_chars=5000)
        # Should not include all 20 contexts
        assert len(user) < 10000


class TestExtractSources:

    def test_extracts_unique_sources(self):
        contexts = [
            RetrievedContext(text="a", file_path="a.py", start_line=1, end_line=5,
                             symbol_name="x", symbol_type="function", language="Python", relevance_score=0.9),
            RetrievedContext(text="b", file_path="b.py", start_line=10, end_line=20,
                             symbol_name="y", symbol_type="class", language="Python", relevance_score=0.8),
            # Duplicate
            RetrievedContext(text="a", file_path="a.py", start_line=1, end_line=5,
                             symbol_name="x", symbol_type="function", language="Python", relevance_score=0.7),
        ]
        sources = extract_sources(contexts)
        assert len(sources) == 2

    def test_source_structure(self):
        contexts = [
            RetrievedContext(text="a", file_path="app.py", start_line=1, end_line=5,
                             symbol_name="run", symbol_type="function", language="Python", relevance_score=0.9),
        ]
        sources = extract_sources(contexts)
        assert sources[0]["file_path"] == "app.py"
        assert sources[0]["start_line"] == 1
        assert sources[0]["end_line"] == 5
        assert sources[0]["symbol_name"] == "run"


class TestBuildRepoSummary:

    def test_includes_stats(self):
        stats = {
            "name": "MyRepo",
            "primary_language": "Python",
            "total_files": 42,
            "total_lines": 5000,
            "frameworks": ["FastAPI", "React"],
            "package_managers": ["pip"],
            "total_functions": 100,
            "total_classes": 20,
            "total_methods": 50,
        }
        summary = build_repo_summary(stats)
        assert "MyRepo" in summary
        assert "Python" in summary
        assert "FastAPI" in summary
        assert "100" in summary

    def test_handles_empty_stats(self):
        summary = build_repo_summary({})
        assert summary == ""
