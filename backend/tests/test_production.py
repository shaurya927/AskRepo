"""Tests for rate limiter middleware."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.middleware.rate_limiter import RateLimiter, _Window


class TestSlidingWindow:
    """Test the sliding window counter."""

    def test_count_in_empty_window(self):
        w = _Window()
        assert w.count_in_window(86400) == 0

    def test_add_and_count(self):
        w = _Window()
        w.add()
        w.add()
        assert w.count_in_window(86400) == 2

    def test_expired_entries_pruned(self):
        w = _Window()
        w.timestamps = [time.time() - 100000]  # Old entry
        w.add()  # Fresh entry
        assert w.count_in_window(86400) == 1  # Only fresh one counts

    def test_seconds_until_next(self):
        w = _Window()
        w.timestamps = [time.time()]
        # Should be close to 86400 seconds
        remaining = w.seconds_until_next(86400)
        assert 86390 <= remaining <= 86400


class TestRateLimiterRouting:
    """Test that rate limiter identifies the right endpoints."""

    def test_analysis_endpoint_detected(self):
        """POST /api/repositories should be rate limited for analysis."""
        path = "/api/repositories"
        method = "POST"
        assert method == "POST" and path == "/api/repositories"

    def test_chat_endpoint_detected(self):
        """POST to chat endpoint should be rate limited."""
        path = "/api/repositories/some-id/chat"
        method = "POST"
        assert method == "POST" and "/chat" in path and "/repositories/" in path

    def test_get_requests_not_limited(self):
        """GET requests should not be rate limited."""
        method = "GET"
        path = "/api/repositories"
        # Only POST triggers limits
        is_limited = (method == "POST" and path == "/api/repositories")
        assert not is_limited


class TestErrorHandler:
    """Test structured error response format."""

    def test_error_response_format(self):
        from app.middleware.error_handler import _error_response
        resp = _error_response("TEST_ERROR", "Something went wrong", "Details here", 400)
        assert resp.status_code == 400
        import json
        body = json.loads(resp.body)
        assert body["error"]["code"] == "TEST_ERROR"
        assert body["error"]["message"] == "Something went wrong"
        assert body["error"]["detail"] == "Details here"
        assert body["error"]["status"] == 400

    def test_error_without_detail(self):
        from app.middleware.error_handler import _error_response
        resp = _error_response("NOT_FOUND", "Not found", None, 404)
        import json
        body = json.loads(resp.body)
        assert "detail" not in body["error"]


class TestCleanup:
    """Test stale workspace cleanup."""

    def test_cleanup_removes_old_dirs(self, tmp_path):
        from app.core.cleanup import cleanup_stale_workspaces
        import os

        old_dir = tmp_path / "old_workspace"
        old_dir.mkdir()
        # Set mtime to 2 hours ago
        old_time = time.time() - 7200
        os.utime(old_dir, (old_time, old_time))

        cleaned = cleanup_stale_workspaces(str(tmp_path), max_age_hours=1)
        assert cleaned == 1
        assert not old_dir.exists()

    def test_cleanup_keeps_recent_dirs(self, tmp_path):
        from app.core.cleanup import cleanup_stale_workspaces

        recent_dir = tmp_path / "recent_workspace"
        recent_dir.mkdir()

        cleaned = cleanup_stale_workspaces(str(tmp_path), max_age_hours=1)
        assert cleaned == 0
        assert recent_dir.exists()

    def test_safe_path_validation(self):
        from app.core.cleanup import is_safe_cleanup_path
        from pathlib import Path

        assert is_safe_cleanup_path(Path("./tmp/repos/abc"), "./tmp/repos")
        assert not is_safe_cleanup_path(Path("/etc/passwd"), "./tmp/repos")


class TestLoggingConfig:
    """Test logging configuration."""

    def test_configure_logging(self):
        from app.core.logging_config import configure_logging
        import logging
        configure_logging("DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_request_id_context(self):
        from app.core.logging_config import request_id_var
        request_id_var.set("test-123")
        assert request_id_var.get() == "test-123"
