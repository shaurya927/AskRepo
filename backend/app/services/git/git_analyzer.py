"""Git analyzer — extracts commit history, file changes, hotspots, and co-changes."""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from git import Repo, InvalidGitRepositoryError, GitCommandError

logger = logging.getLogger(__name__)


@dataclass
class CommitData:
    sha: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    committed_date: datetime
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


@dataclass
class FileChangeData:
    commit_sha: str
    file_path: str
    change_type: str  # added, modified, deleted, renamed
    insertions: int = 0
    deletions: int = 0
    patch: str | None = None


@dataclass
class GitAnalysisResult:
    commits: list[CommitData] = field(default_factory=list)
    file_changes: list[FileChangeData] = field(default_factory=list)
    has_history: bool = False


class GitAnalyzer:
    """Analyzes git history from a cloned repository."""

    def __init__(self, max_diff_size: int = 50000):
        self.max_diff_size = max_diff_size

    def analyze_history(
        self, repo_path: Path, max_commits: int = 200
    ) -> GitAnalysisResult:
        """Extract commit history and file changes from a git repository.

        Args:
            repo_path: Path to the cloned repository.
            max_commits: Maximum number of commits to analyze.

        Returns:
            GitAnalysisResult with commits and file changes.
        """
        result = GitAnalysisResult()

        try:
            repo = Repo(str(repo_path))
        except (InvalidGitRepositoryError, Exception) as e:
            logger.info(f"Not a git repository or no history: {e}")
            return result

        if repo.bare:
            logger.info("Bare repository, skipping history analysis")
            return result

        try:
            commits_iter = repo.iter_commits(max_count=max_commits)
        except Exception as e:
            logger.warning(f"Failed to iterate commits: {e}")
            return result

        result.has_history = True

        for commit in commits_iter:
            # Extract commit metadata
            authored = commit.authored_datetime
            if authored.tzinfo is None:
                authored = authored.replace(tzinfo=None)
            committed = commit.committed_datetime
            if committed.tzinfo is None:
                committed = committed.replace(tzinfo=None)

            cd = CommitData(
                sha=commit.hexsha,
                message=commit.message.strip(),
                author_name=commit.author.name or "Unknown",
                author_email=commit.author.email or "",
                authored_date=authored,
                committed_date=committed,
            )

            # Extract diff stats efficiently using commit.stats.files
            try:
                stats = commit.stats.files
                cd.files_changed = len(stats)
                
                for file_path, stat in stats.items():
                    # Guess change type (stats doesn't give precise type)
                    # We will default to modified.
                    change_type = "modified"
                    if stat.get("insertions", 0) > 0 and stat.get("deletions", 0) == 0 and stat.get("lines", 0) == stat.get("insertions", 0):
                        change_type = "added"
                    
                    fc = FileChangeData(
                        commit_sha=cd.sha,
                        file_path=file_path,
                        change_type=change_type,
                        insertions=stat.get("insertions", 0),
                        deletions=stat.get("deletions", 0),
                        patch=None  # Skip patch to save massive amounts of memory
                    )
                    cd.insertions += fc.insertions
                    cd.deletions += fc.deletions
                    result.file_changes.append(fc)
            except Exception as e:
                logger.warning(f"Error extracting diff for commit {cd.sha}: {e}")

            result.commits.append(cd)

        logger.info(f"Analyzed {len(result.commits)} commits, {len(result.file_changes)} file changes")
        return result

    @staticmethod
    def get_change_frequency(file_changes: list[dict]) -> list[dict]:
        """Rank files by how frequently they change (hotspots).

        Args:
            file_changes: List of dicts with file_path, insertions, deletions.

        Returns:
            Sorted list of {file_path, change_count, total_insertions, total_deletions}.
        """
        freq: dict[str, dict] = {}
        for fc in file_changes:
            fp = fc["file_path"]
            if fp not in freq:
                freq[fp] = {"file_path": fp, "change_count": 0, "total_insertions": 0, "total_deletions": 0}
            freq[fp]["change_count"] += 1
            freq[fp]["total_insertions"] += fc.get("insertions", 0)
            freq[fp]["total_deletions"] += fc.get("deletions", 0)

        return sorted(freq.values(), key=lambda x: x["change_count"], reverse=True)

    @staticmethod
    def get_co_change_pairs(file_changes: list[dict]) -> list[dict]:
        """Find files that frequently change together within the same commit.

        Args:
            file_changes: List of dicts with commit_sha, file_path.

        Returns:
            Sorted list of {file_a, file_b, co_change_count}.
        """
        # Group files by commit
        commit_files: dict[str, list[str]] = defaultdict(list)
        for fc in file_changes:
            commit_files[fc["commit_sha"]].append(fc["file_path"])

        # Count co-occurrences
        pair_counts: Counter = Counter()
        for files in commit_files.values():
            unique = sorted(set(files))
            for i in range(len(unique)):
                for j in range(i + 1, len(unique)):
                    pair_counts[(unique[i], unique[j])] += 1

        # Filter to pairs that co-changed at least 2 times
        results = []
        for (a, b), count in pair_counts.most_common(50):
            if count >= 2:
                results.append({"file_a": a, "file_b": b, "co_change_count": count})

        return results

    @staticmethod
    def get_commit_timeline(commits: list[dict]) -> list[dict]:
        """Group commits by ISO week for timeline visualization.

        Args:
            commits: List of dicts with authored_date, insertions, deletions.

        Returns:
            Sorted list of {week, commit_count, insertions, deletions}.
        """
        weeks: dict[str, dict] = {}
        for c in commits:
            dt = c.get("authored_date")
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt is None:
                continue
            iso = dt.isocalendar()
            week_key = f"{iso[0]}-W{iso[1]:02d}"
            if week_key not in weeks:
                weeks[week_key] = {"week": week_key, "commit_count": 0, "insertions": 0, "deletions": 0}
            weeks[week_key]["commit_count"] += 1
            weeks[week_key]["insertions"] += c.get("insertions", 0)
            weeks[week_key]["deletions"] += c.get("deletions", 0)

        return sorted(weeks.values(), key=lambda x: x["week"])
