"""
Test suite for the main module
"""

import pytest
from unittest.mock import patch
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import main


def test_main_missing_database_url():
    """Test that main raises ValueError when DATABASE_URL is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="DATABASE_URL"):
            main()


def test_main_missing_youtube_api_key():
    """Test that main raises ValueError when YOUTUBE_API_KEY is not set."""
    with patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://localhost/test"}, clear=True
    ):
        with pytest.raises(ValueError, match="YOUTUBE_API_KEY"):
            main()


def test_main_with_config(capsys):
    """Test that main runs successfully with proper configuration."""
    env_vars = {
        "DATABASE_URL": "postgresql://user:pass@localhost/dbname",
        "YOUTUBE_API_KEY": "test_api_key_123",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        main()
        captured = capsys.readouterr()
        assert "Butbul Halacha Ingest - Starting..." in captured.out
        assert "Database URL:" in captured.out
        assert "YouTube API Key configured: Yes" in captured.out
