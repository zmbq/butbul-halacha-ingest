"""Configuration module for Butbul Halacha Ingest.

This module exposes a Config object which loads required secrets from
environment variables and provides a default, non-secret YouTube
channel identifier that is safe to store in code.
"""

import os
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""

    def __init__(self):
        # Load environment variables from .env file (if present)
        load_dotenv()

        # Required secrets / config
        self.database_url: str = self._get_required_env("DATABASE_URL")
        self.youtube_api_key: str = self._get_required_env("YOUTUBE_API_KEY")
        self.openai_api_key: str = self._get_required_env("OPENAI_API_KEY")

        # Public channel ID: treated as non-secret. Default is embedded here
        # but can be overridden via the environment variable YOUTUBE_CHANNEL_ID.
        self.youtube_channel_id: str = os.getenv(
            "YOUTUBE_CHANNEL_ID", "UCS9moGQA0U4MqWzT98mIlGw"
        )

        # Data directory (defaults to a `data/` sibling of the repo root)
        env_data_dir = self._get_optional_env("DATA_DIR")
        if env_data_dir:
            self.data_dir: Path = Path(env_data_dir).expanduser().resolve()
        else:
            project_root = Path(__file__).resolve().parent.parent
            self.data_dir: Path = (project_root / "data").resolve()

    @staticmethod
    def _get_required_env(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    @staticmethod
    def _get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)

    def __repr__(self) -> str:
        return (
            f"Config(database_url='{self._mask_value(self.database_url)}', "
            f"youtube_api_key='{self._mask_value(self.youtube_api_key)}', "
            f"openai_api_key='{self._mask_value(self.openai_api_key)}', "
            f"youtube_channel_id='{self.youtube_channel_id}', "
            f"data_dir='{self.data_dir}')"
        )

    @staticmethod
    def _mask_value(value: str, visible_chars: int = 4) -> str:
        if len(value) <= visible_chars:
            return "***"
        return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"


# Single, importable config instance
config = Config()
