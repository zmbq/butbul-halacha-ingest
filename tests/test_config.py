"""
Tests for the configuration module.
"""

import pytest
import os
from unittest.mock import patch


def test_config_loads_required_variables():
    """Test that config loads all required environment variables."""
    env_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_db",
        "YOUTUBE_API_KEY": "test_api_key_12345",
        "YOUTUBE_CHANNEL_ID": "test_channel_id",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        # Import config inside the test to ensure it uses the patched environment
        from src.config import Config

        test_config = Config()

        assert test_config.database_url == env_vars["DATABASE_URL"]
        assert test_config.youtube_api_key == env_vars["YOUTUBE_API_KEY"]
        assert test_config.youtube_channel_id == env_vars["YOUTUBE_CHANNEL_ID"]


def test_config_raises_error_for_missing_required_variable():
    """Test that config raises ValueError when required variables are missing."""
    env_vars = {
        "YOUTUBE_API_KEY": "test_api_key",
        "YOUTUBE_CHANNEL_ID": "test_channel",
        # DATABASE_URL is missing
    }

    # Mock load_dotenv to prevent loading from .env file
    with patch.dict(os.environ, env_vars, clear=True), \
         patch("src.config.load_dotenv"):
        from src.config import Config

        with pytest.raises(ValueError, match="DATABASE_URL"):
            Config()


def test_config_masks_sensitive_values_in_repr():
    """Test that config masks sensitive values when converted to string."""
    env_vars = {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/db",
        "YOUTUBE_API_KEY": "very_secret_api_key_12345",
        "YOUTUBE_CHANNEL_ID": "UCxxxxxxxx",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        from src.config import Config

        test_config = Config()
        config_str = repr(test_config)

        # Check that sensitive values are masked
        assert "post*****" in config_str or "****" in config_str
        assert "very_secret_api_key_12345" not in config_str
        # Channel ID is not sensitive, so it should be visible
        assert "UCxxxxxxxx" in config_str
