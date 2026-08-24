"""Tests for security utilities."""

from app.core.security import is_path_traversal, is_binary_extension, sanitize_filename


class TestPathTraversal:
    def test_detects_dotdot(self):
        assert is_path_traversal("../etc/passwd") is True

    def test_detects_dotdot_in_middle(self):
        assert is_path_traversal("foo/../bar") is True

    def test_detects_absolute_path(self):
        assert is_path_traversal("/etc/passwd") is True

    def test_allows_normal_path(self):
        assert is_path_traversal("src/main.py") is False

    def test_allows_dotfile(self):
        assert is_path_traversal(".gitignore") is False

    def test_allows_nested_path(self):
        assert is_path_traversal("src/components/Header.tsx") is False


class TestBinaryExtension:
    def test_detects_png(self):
        assert is_binary_extension(".png") is True

    def test_detects_exe(self):
        assert is_binary_extension(".exe") is True

    def test_detects_case_insensitive(self):
        assert is_binary_extension(".PNG") is True

    def test_allows_python(self):
        assert is_binary_extension(".py") is False

    def test_allows_javascript(self):
        assert is_binary_extension(".js") is False


class TestSanitizeFilename:
    def test_removes_special_chars(self):
        assert sanitize_filename("my file (1).txt") == "my_file__1_.txt"

    def test_preserves_normal_name(self):
        assert sanitize_filename("main.py") == "main.py"

    def test_handles_dots_and_dashes(self):
        assert sanitize_filename("my-file.test.py") == "my-file.test.py"
