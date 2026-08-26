"""Tests for the git analyzer."""

import os
from datetime import datetime, timezone
from pathlib import Path

from git import Repo

from app.services.git.git_analyzer import GitAnalyzer


def _create_test_repo(tmp_path: Path) -> Path:
    """Create a small git repo with a few commits for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    repo = Repo.init(str(repo_dir))

    # Configure git user
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    # Commit 1: add main.py
    (repo_dir / "main.py").write_text("print('hello')\n")
    repo.index.add(["main.py"])
    repo.index.commit("Initial commit: add main.py")

    # Commit 2: add utils.py and modify main.py
    (repo_dir / "utils.py").write_text("def helper(): pass\n")
    (repo_dir / "main.py").write_text("from utils import helper\nprint('hello')\n")
    repo.index.add(["main.py", "utils.py"])
    repo.index.commit("Add utils and update main")

    # Commit 3: modify utils.py
    (repo_dir / "utils.py").write_text("def helper(): return 42\ndef extra(): pass\n")
    repo.index.add(["utils.py"])
    repo.index.commit("Update utils with extra function")

    return repo_dir


class TestGitAnalyzer:

    def test_analyze_history(self, tmp_path):
        repo_dir = _create_test_repo(tmp_path)
        analyzer = GitAnalyzer()
        result = analyzer.analyze_history(repo_dir, max_commits=100)

        assert result.has_history
        assert len(result.commits) == 3
        # Newest first
        assert "Update utils" in result.commits[0].message
        assert "Add utils" in result.commits[1].message
        assert "Initial commit" in result.commits[2].message

    def test_commit_metadata(self, tmp_path):
        repo_dir = _create_test_repo(tmp_path)
        analyzer = GitAnalyzer()
        result = analyzer.analyze_history(repo_dir)

        c = result.commits[0]
        assert c.author_name == "Test User"
        assert c.author_email == "test@example.com"
        assert len(c.sha) == 40
        assert c.authored_date is not None

    def test_file_changes(self, tmp_path):
        repo_dir = _create_test_repo(tmp_path)
        analyzer = GitAnalyzer()
        result = analyzer.analyze_history(repo_dir)

        assert len(result.file_changes) > 0
        # Initial commit should have main.py as "added"
        initial_changes = [fc for fc in result.file_changes if "Initial" in
                           next((c.message for c in result.commits if c.sha == fc.commit_sha), "")]
        assert any(fc.file_path == "main.py" for fc in initial_changes)

    def test_non_git_directory(self, tmp_path):
        """Non-git directories should return empty result."""
        plain_dir = tmp_path / "not_git"
        plain_dir.mkdir()
        analyzer = GitAnalyzer()
        result = analyzer.analyze_history(plain_dir)
        assert not result.has_history
        assert len(result.commits) == 0

    def test_max_commits_limit(self, tmp_path):
        repo_dir = _create_test_repo(tmp_path)
        analyzer = GitAnalyzer()
        result = analyzer.analyze_history(repo_dir, max_commits=2)
        assert len(result.commits) == 2

    def test_diff_size_limit(self, tmp_path):
        repo_dir = _create_test_repo(tmp_path)
        # Use very small limit to test truncation
        analyzer = GitAnalyzer(max_diff_size=10)
        result = analyzer.analyze_history(repo_dir)
        # Patches longer than 10 chars should be None
        for fc in result.file_changes:
            if fc.patch is not None:
                assert len(fc.patch) <= 10


class TestChangeFrequency:

    def test_ranks_by_frequency(self):
        file_changes = [
            {"file_path": "a.py", "insertions": 5, "deletions": 2},
            {"file_path": "a.py", "insertions": 3, "deletions": 1},
            {"file_path": "a.py", "insertions": 1, "deletions": 0},
            {"file_path": "b.py", "insertions": 10, "deletions": 5},
        ]
        hotspots = GitAnalyzer.get_change_frequency(file_changes)
        assert hotspots[0]["file_path"] == "a.py"
        assert hotspots[0]["change_count"] == 3
        assert hotspots[1]["file_path"] == "b.py"
        assert hotspots[1]["change_count"] == 1

    def test_totals_insertions_deletions(self):
        file_changes = [
            {"file_path": "x.py", "insertions": 5, "deletions": 2},
            {"file_path": "x.py", "insertions": 3, "deletions": 1},
        ]
        hotspots = GitAnalyzer.get_change_frequency(file_changes)
        assert hotspots[0]["total_insertions"] == 8
        assert hotspots[0]["total_deletions"] == 3


class TestCoChangePairs:

    def test_detects_co_changes(self):
        file_changes = [
            {"commit_sha": "aaa", "file_path": "a.py"},
            {"commit_sha": "aaa", "file_path": "b.py"},
            {"commit_sha": "bbb", "file_path": "a.py"},
            {"commit_sha": "bbb", "file_path": "b.py"},
            {"commit_sha": "ccc", "file_path": "c.py"},
        ]
        co_changes = GitAnalyzer.get_co_change_pairs(file_changes)
        assert len(co_changes) == 1
        assert co_changes[0]["file_a"] == "a.py"
        assert co_changes[0]["file_b"] == "b.py"
        assert co_changes[0]["co_change_count"] == 2

    def test_ignores_single_co_changes(self):
        file_changes = [
            {"commit_sha": "aaa", "file_path": "a.py"},
            {"commit_sha": "aaa", "file_path": "b.py"},
        ]
        co_changes = GitAnalyzer.get_co_change_pairs(file_changes)
        # Only 1 co-change, below threshold of 2
        assert len(co_changes) == 0


class TestCommitTimeline:

    def test_groups_by_week(self):
        commits = [
            {"authored_date": datetime(2024, 1, 1, tzinfo=timezone.utc), "insertions": 10, "deletions": 5},
            {"authored_date": datetime(2024, 1, 2, tzinfo=timezone.utc), "insertions": 3, "deletions": 1},
            {"authored_date": datetime(2024, 1, 15, tzinfo=timezone.utc), "insertions": 20, "deletions": 10},
        ]
        timeline = GitAnalyzer.get_commit_timeline(commits)
        assert len(timeline) >= 2  # At least 2 different weeks
        # Each entry has required keys
        for entry in timeline:
            assert "week" in entry
            assert "commit_count" in entry
            assert "insertions" in entry
