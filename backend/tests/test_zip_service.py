"""Tests for ZIP service security protections."""

import zipfile
import tempfile
from pathlib import Path

import pytest

from app.services.repository.zip_service import ZipService


class TestZipExtraction:
    def setup_method(self):
        self.svc = ZipService()

    def test_rejects_invalid_zip(self, tmp_path):
        fake_zip = tmp_path / "fake.zip"
        fake_zip.write_text("not a zip file")
        with pytest.raises(ValueError, match="Invalid ZIP"):
            self.svc.extract_zip(fake_zip, tmp_path / "out", 50, 2000)

    def test_rejects_path_traversal(self, tmp_path):
        zip_path = tmp_path / "evil.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../../../etc/passwd", "evil content")

        with pytest.raises(ValueError, match="Path traversal"):
            self.svc.extract_zip(zip_path, tmp_path / "out", 50, 2000)

    def test_enforces_file_count_limit(self, tmp_path):
        zip_path = tmp_path / "many.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            for i in range(10):
                zf.writestr(f"file_{i}.txt", f"content {i}")

        with pytest.raises(ValueError, match="more than 5 files"):
            self.svc.extract_zip(zip_path, tmp_path / "out", 50, 5)

    def test_enforces_size_limit(self, tmp_path):
        zip_path = tmp_path / "big.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            # Write 2MB of data
            zf.writestr("bigfile.txt", "x" * (2 * 1024 * 1024))

        with pytest.raises(ValueError, match="exceeds.*limit"):
            # Limit to 1MB
            self.svc.extract_zip(zip_path, tmp_path / "out", 1, 2000)

    def test_extracts_valid_zip(self, tmp_path):
        zip_path = tmp_path / "good.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("src/main.py", "print('hello')")
            zf.writestr("README.md", "# Hello")

        out_dir = tmp_path / "out"
        result = self.svc.extract_zip(zip_path, out_dir, 50, 2000)
        assert (out_dir / "src" / "main.py").exists()
        assert (out_dir / "README.md").exists()


class TestZipValidation:
    def setup_method(self):
        self.svc = ZipService()

    def test_valid_zip(self, tmp_path):
        zip_path = tmp_path / "valid.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("test.txt", "content")
        # Should not raise
        self.svc.validate_zip(zip_path)

    def test_invalid_zip(self, tmp_path):
        fake = tmp_path / "fake.zip"
        fake.write_text("not a zip")
        with pytest.raises(ValueError):
            self.svc.validate_zip(fake)
