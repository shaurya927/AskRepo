"""Tests for file filter."""

from pathlib import Path
from app.services.repository.file_filter import FileFilter


class TestFileFilter:
    def setup_method(self):
        self.filter = FileFilter()

    def test_ignores_git_directory(self):
        assert self.filter.should_ignore_directory(".git") is True

    def test_ignores_node_modules(self):
        assert self.filter.should_ignore_directory("node_modules") is True

    def test_ignores_pycache(self):
        assert self.filter.should_ignore_directory("__pycache__") is True

    def test_ignores_venv(self):
        assert self.filter.should_ignore_directory("venv") is True

    def test_ignores_dist(self):
        assert self.filter.should_ignore_directory("dist") is True

    def test_ignores_build(self):
        assert self.filter.should_ignore_directory("build") is True

    def test_ignores_next(self):
        assert self.filter.should_ignore_directory(".next") is True

    def test_ignores_target(self):
        assert self.filter.should_ignore_directory("target") is True

    def test_ignores_coverage(self):
        assert self.filter.should_ignore_directory("coverage") is True

    def test_allows_src(self):
        assert self.filter.should_ignore_directory("src") is False

    def test_allows_lib(self):
        assert self.filter.should_ignore_directory("lib") is False

    def test_allows_app(self):
        assert self.filter.should_ignore_directory("app") is False

    def test_custom_ignored_dirs(self):
        custom_filter = FileFilter(ignored_dirs={"custom_dir"})
        assert custom_filter.should_ignore_directory("custom_dir") is True
        assert custom_filter.should_ignore_directory("node_modules") is False
