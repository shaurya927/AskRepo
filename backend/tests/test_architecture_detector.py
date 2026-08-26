"""Tests for architecture detector."""

from app.services.graph.architecture_detector import ArchitectureDetector


class TestArchitectureDetector:

    def setup_method(self):
        self.detector = ArchitectureDetector()

    def test_detects_frontend(self):
        files = [
            {"path": "src/components/Button.tsx", "language": "TypeScript"},
            {"path": "src/pages/Home.tsx", "language": "TypeScript"},
        ]
        result = self.detector.detect(files)
        assert "frontend" in result
        assert len(result["frontend"]) == 2

    def test_detects_api(self):
        files = [
            {"path": "app/api/endpoints/users.py", "language": "Python"},
            {"path": "app/api/endpoints/auth.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "api" in result

    def test_detects_tests(self):
        files = [
            {"path": "tests/test_main.py", "language": "Python"},
            {"path": "src/__tests__/app.test.ts", "language": "TypeScript"},
        ]
        result = self.detector.detect(files)
        assert "tests" in result
        assert len(result["tests"]) == 2

    def test_detects_models(self):
        files = [
            {"path": "app/models/user.py", "language": "Python"},
            {"path": "app/schemas/user.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "models" in result

    def test_detects_config(self):
        files = [
            {"path": "pyproject.toml", "language": ""},
            {"path": "app/core/config.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "config" in result

    def test_detects_services(self):
        files = [
            {"path": "app/services/auth_service.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "services" in result

    def test_detects_infrastructure(self):
        files = [
            {"path": "Dockerfile", "language": ""},
            {"path": ".github/workflows/ci.yml", "language": ""},
        ]
        result = self.detector.detect(files)
        assert "infrastructure" in result

    def test_detects_authentication(self):
        files = [
            {"path": "src/auth/login.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "authentication" in result

    def test_import_based_detection(self):
        files = [
            {"path": "server.py", "language": "Python"},
        ]
        imports = [
            {"file_path": "server.py", "source": "fastapi", "is_internal": False},
        ]
        result = self.detector.detect(files, imports=imports)
        assert "backend" in result

    def test_summary(self):
        files = [
            {"path": "src/components/App.tsx", "language": "TypeScript"},
            {"path": "src/components/Home.tsx", "language": "TypeScript"},
            {"path": "tests/test_app.py", "language": "Python"},
        ]
        detection = self.detector.detect(files)
        summary = self.detector.get_architecture_summary(detection)
        assert summary["total_classified"] > 0
        assert len(summary["categories"]) > 0
        # Categories should have counts
        for cat in summary["categories"]:
            assert "name" in cat
            assert "file_count" in cat
            assert "percentage" in cat

    def test_unknown_falls_to_backend(self):
        """Python files in root directory should fall to backend."""
        files = [
            {"path": "main.py", "language": "Python"},
        ]
        result = self.detector.detect(files)
        assert "backend" in result
