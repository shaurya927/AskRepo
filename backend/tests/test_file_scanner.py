"""Tests for file scanner language detection and file identification."""

from pathlib import Path

from app.services.repository.file_scanner import FileScanner


class TestLanguageDetection:
    def setup_method(self):
        self.scanner = FileScanner()

    def test_python(self):
        assert self.scanner.detect_language(Path("main.py")) == "Python"

    def test_javascript(self):
        assert self.scanner.detect_language(Path("app.js")) == "JavaScript"

    def test_typescript(self):
        assert self.scanner.detect_language(Path("app.ts")) == "TypeScript"

    def test_tsx(self):
        assert self.scanner.detect_language(Path("Component.tsx")) == "TypeScript"

    def test_jsx(self):
        assert self.scanner.detect_language(Path("Component.jsx")) == "JavaScript"

    def test_java(self):
        assert self.scanner.detect_language(Path("Main.java")) == "Java"

    def test_cpp(self):
        assert self.scanner.detect_language(Path("main.cpp")) == "C++"

    def test_go(self):
        assert self.scanner.detect_language(Path("main.go")) == "Go"

    def test_rust(self):
        assert self.scanner.detect_language(Path("main.rs")) == "Rust"

    def test_dockerfile(self):
        assert self.scanner.detect_language(Path("Dockerfile")) == "Dockerfile"

    def test_unknown(self):
        assert self.scanner.detect_language(Path("README")) is None

    def test_yaml(self):
        assert self.scanner.detect_language(Path("config.yml")) == "YAML"

    def test_json(self):
        assert self.scanner.detect_language(Path("package.json")) == "JSON"


class TestTestFileDetection:
    def setup_method(self):
        self.scanner = FileScanner()

    def test_python_test(self):
        assert self.scanner._is_test_file(Path("test_main.py"), "test_main.py") is True

    def test_python_test_suffix(self):
        assert self.scanner._is_test_file(Path("main_test.py"), "main_test.py") is True

    def test_js_spec(self):
        assert self.scanner._is_test_file(Path("app.spec.js"), "app.spec.js") is True

    def test_js_test(self):
        assert self.scanner._is_test_file(Path("app.test.js"), "app.test.js") is True

    def test_tests_directory(self):
        assert self.scanner._is_test_file(Path("tests/test_main.py"), "tests/test_main.py") is True

    def test_regular_file(self):
        assert self.scanner._is_test_file(Path("main.py"), "src/main.py") is False

    def test_dunder_tests_dir(self):
        assert self.scanner._is_test_file(
            Path("src/__tests__/App.test.tsx"),
            "src/__tests__/App.test.tsx",
        ) is True


class TestFrameworkDetection:
    def setup_method(self):
        self.scanner = FileScanner()

    def test_detects_from_package_json(self, tmp_path):
        pkg = tmp_path / "package.json"
        pkg.write_text('{"dependencies": {"react": "^18.0.0", "next": "^14.0.0"}}')
        result = self.scanner.detect_frameworks(tmp_path, [])
        assert "React" in result
        assert "Next.js" in result

    def test_detects_python_frameworks(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.100.0\nsqlalchemy==2.0.0\n")
        result = self.scanner.detect_frameworks(tmp_path, [])
        assert "FastAPI" in result
        assert "SQLAlchemy" in result

    def test_no_frameworks(self, tmp_path):
        result = self.scanner.detect_frameworks(tmp_path, [])
        assert result == []


class TestPackageManagerDetection:
    def setup_method(self):
        self.scanner = FileScanner()

    def test_detects_npm(self, tmp_path):
        (tmp_path / "package-lock.json").write_text("{}")
        result = self.scanner.detect_package_managers(tmp_path)
        assert "npm" in result

    def test_detects_pip(self, tmp_path):
        (tmp_path / "requirements.txt").write_text("flask\n")
        result = self.scanner.detect_package_managers(tmp_path)
        assert "pip" in result

    def test_detects_cargo(self, tmp_path):
        (tmp_path / "Cargo.toml").write_text("[package]\n")
        result = self.scanner.detect_package_managers(tmp_path)
        assert "Cargo" in result

    def test_no_managers(self, tmp_path):
        result = self.scanner.detect_package_managers(tmp_path)
        assert result == []
