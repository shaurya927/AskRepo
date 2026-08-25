"""Tests for dependency resolver."""

from pathlib import Path

from app.services.parser.base import ParsedImport
from app.services.analysis.dependency_resolver import DependencyResolver


class TestDependencyResolver:
    def setup_method(self):
        self.resolver = DependencyResolver()

    def test_resolves_python_import(self):
        imp = ParsedImport(
            source="app.core.config", names=["Settings"],
            is_relative=False, file_path="app/main.py", line=1,
        )
        file_paths = {"app/core/config.py", "app/main.py"}
        result = self.resolver.resolve([imp], file_paths, Path("/repo"))
        assert len(result) == 1
        assert result[0].is_internal is True
        assert result[0].resolved_path == "app/core/config.py"

    def test_resolves_python_package_import(self):
        imp = ParsedImport(
            source="app.models", names=["Repository"],
            is_relative=False, file_path="app/main.py", line=1,
        )
        file_paths = {"app/models/__init__.py", "app/main.py"}
        result = self.resolver.resolve([imp], file_paths, Path("/repo"))
        assert len(result) == 1
        assert result[0].is_internal is True
        assert result[0].resolved_path == "app/models/__init__.py"

    def test_marks_external_imports(self):
        imp = ParsedImport(
            source="fastapi", names=["FastAPI"],
            is_relative=False, file_path="app/main.py", line=1,
        )
        file_paths = {"app/main.py"}
        result = self.resolver.resolve([imp], file_paths, Path("/repo"))
        assert len(result) == 1
        assert result[0].is_internal is False
        assert result[0].resolved_path is None

    def test_resolves_js_relative_import(self):
        imp = ParsedImport(
            source="./utils", names=["formatDate"],
            is_relative=True, file_path="src/app.ts", line=1,
        )
        file_paths = {"src/app.ts", "src/utils.ts"}
        result = self.resolver.resolve([imp], file_paths, Path("/repo"))
        assert len(result) == 1
        assert result[0].is_internal is True

    def test_handles_missing_files(self):
        imp = ParsedImport(
            source="./nonexistent", names=["something"],
            is_relative=True, file_path="src/app.js", line=1,
        )
        file_paths = {"src/app.js"}
        result = self.resolver.resolve([imp], file_paths, Path("/repo"))
        assert len(result) == 1
        assert result[0].is_internal is False
