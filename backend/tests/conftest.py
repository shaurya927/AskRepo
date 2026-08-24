"""Test fixtures and configuration."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def settings():
    """Create a mock settings object for testing."""
    s = MagicMock()
    s.APP_NAME = "AskRepo"
    s.APP_VERSION = "0.1.0"
    s.DATABASE_URL = "sqlite+aiosqlite:///test.db"
    s.MAX_REPOSITORY_SIZE_MB = 50
    s.MAX_FILE_COUNT = 2000
    s.MAX_FILE_SIZE_MB = 1
    s.TEMP_REPOSITORY_PATH = "./tmp/test_repos"
    s.GITHUB_TOKEN = None
    return s
