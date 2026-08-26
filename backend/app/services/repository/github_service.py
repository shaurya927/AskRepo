"""GitHub service: URL validation, API checks, repository cloning."""

import re
from pathlib import Path

import httpx
from git import Repo


class GitHubService:
    """Handles GitHub repository validation and cloning."""

    # Match: https://github.com/{owner}/{repo} with optional trailing slash and .git
    URL_PATTERN = re.compile(
        r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+(\.git)?/?$"
    )

    def validate_url(self, url: str) -> bool:
        """Check if a URL is a valid GitHub repository URL."""
        return bool(self.URL_PATTERN.match(url))

    def parse_url(self, url: str) -> tuple[str, str]:
        """Extract (owner, repo) from a GitHub URL."""
        cleaned = url.rstrip("/")
        if cleaned.endswith(".git"):
            cleaned = cleaned[:-4]
        parts = cleaned.split("/")
        return parts[-2], parts[-1]

    async def check_repository_exists(
        self, url: str, token: str | None = None
    ) -> dict:
        """Verify a GitHub repository exists and is accessible.
        
        Returns the GitHub API response as a dict (includes size, description, etc).
        Raises ValueError if the repo is not found or URL is invalid.
        """
        if not self.validate_url(url):
            raise ValueError("Invalid GitHub URL")

        owner, repo = self.parse_url(url)
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers=headers,
            )
            if resp.status_code == 404:
                raise ValueError("Repository not found or is private")
            if resp.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded. Try adding a GITHUB_TOKEN.")
            resp.raise_for_status()
            return resp.json()

    def clone_repository(self, url: str, target_dir: Path, depth: int = 200) -> Path:
        """Clone a repository to target_dir with configurable history depth.

        Args:
            url: GitHub repository URL.
            target_dir: Directory to clone into.
            depth: Number of commits to fetch (default: 200 for git archaeology).
        """
        Repo.clone_from(
            url,
            str(target_dir),
            depth=depth,
            no_checkout=False,
        )
        return target_dir
