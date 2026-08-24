"""Tests for GitHub service URL validation and parsing."""

from app.services.repository.github_service import GitHubService


class TestGitHubURLValidation:
    def setup_method(self):
        self.svc = GitHubService()

    def test_valid_url(self):
        assert self.svc.validate_url("https://github.com/user/repo") is True

    def test_valid_url_with_trailing_slash(self):
        assert self.svc.validate_url("https://github.com/user/repo/") is True

    def test_valid_url_with_dot_git(self):
        assert self.svc.validate_url("https://github.com/user/repo.git") is True

    def test_valid_url_with_dashes(self):
        assert self.svc.validate_url("https://github.com/my-org/my-repo") is True

    def test_valid_url_with_dots(self):
        assert self.svc.validate_url("https://github.com/user/repo.js") is True

    def test_invalid_not_github(self):
        assert self.svc.validate_url("https://gitlab.com/user/repo") is False

    def test_invalid_missing_repo(self):
        assert self.svc.validate_url("https://github.com/user") is False

    def test_invalid_empty(self):
        assert self.svc.validate_url("") is False

    def test_invalid_random_string(self):
        assert self.svc.validate_url("not a url at all") is False

    def test_invalid_with_extra_path(self):
        assert self.svc.validate_url("https://github.com/user/repo/tree/main") is False


class TestGitHubURLParsing:
    def setup_method(self):
        self.svc = GitHubService()

    def test_parse_standard_url(self):
        owner, repo = self.svc.parse_url("https://github.com/expressjs/express")
        assert owner == "expressjs"
        assert repo == "express"

    def test_parse_url_with_trailing_slash(self):
        owner, repo = self.svc.parse_url("https://github.com/user/repo/")
        assert owner == "user"
        assert repo == "repo"

    def test_parse_url_with_dot_git(self):
        owner, repo = self.svc.parse_url("https://github.com/user/repo.git")
        assert owner == "user"
        assert repo == "repo"
