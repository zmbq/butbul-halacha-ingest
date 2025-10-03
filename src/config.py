"""
Configuration module for Butbul Halacha Ingest.

This module loads configuration from environment variables (.env file)
and provides a centralized configuration object.
"""

import os
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        """Initialize configuration by loading from .env file."""
        # Load environment variables from .env file
        load_dotenv()

        # Database configuration
        self.database_url: str = self._get_required_env("DATABASE_URL")

        # YouTube API configuration
        self.youtube_api_key: str = self._get_required_env("YOUTUBE_API_KEY")
        self.youtube_channel_id: str = self._get_required_env("YOUTUBE_CHANNEL_ID")
        
        # Data directory (defaults to a `data/` sibling of the `src/` folder)
        # Can be overridden by the DATA_DIR environment variable.
        env_data_dir = self._get_optional_env("DATA_DIR")
        if env_data_dir:
            self.data_dir: Path = Path(env_data_dir).expanduser().resolve()
        else:
            # src/config.py -> project_root/src/config.py ; project_root = parent of src
            project_root = Path(__file__).resolve().parent.parent
            self.data_dir: Path = (project_root / "data").resolve()

    @staticmethod
    def _get_required_env(key: str) -> str:
        """
        Get a required environment variable.

        Args:
            key: The environment variable name

        Returns:
            The value of the environment variable

        Raises:
            ValueError: If the environment variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    @staticmethod
    def _get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an optional environment variable.

        Args:
            key: The environment variable name
            default: Default value if not set

        Returns:
            The value of the environment variable or default
        """
        return os.getenv(key, default)

    def __repr__(self) -> str:
        """Return a string representation of the config (hiding sensitive data)."""
        return (
            f"Config("
            f"database_url='{self._mask_value(self.database_url)}', "
            f"youtube_api_key='{self._mask_value(self.youtube_api_key)}', "
            f"youtube_channel_id='{self.youtube_channel_id}', "
            f"data_dir='{self.data_dir}'"
            f")"
        )

    @staticmethod
    def _mask_value(value: str, visible_chars: int = 4) -> str:
        """
        Mask a sensitive value for display.

        Args:
            value: The value to mask
            visible_chars: Number of characters to show at the start

        Returns:
            Masked string
        """
        if len(value) <= visible_chars:
            return "***"
        return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"


# Global configuration instance
# This can be imported and used throughout the application
config = Config()
