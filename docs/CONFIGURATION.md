# Configuration Guide

This document explains how to configure the Butbul Halacha Ingest application.

## Configuration File

The application uses a `.env` file to store configuration values. This file is not committed to version control for security reasons.

### Creating Your Configuration

1. Copy the example configuration file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your actual values (the channel id is optional):
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://username:password@host:port/database_name
   
   # YouTube API Configuration
  YOUTUBE_API_KEY=your_actual_youtube_api_key
  # YOUTUBE_CHANNEL_ID is optional; the project defaults to a public channel id
  # but you can override it here if needed:
  # YOUTUBE_CHANNEL_ID=actual_channel_id
   ```

## Configuration Variables

### Required Variables

All of the following environment variables are required:

- **`DATABASE_URL`**: PostgreSQL connection string
  - Format: `postgresql://username:password@host:port/database_name`
  - Example: `postgresql://myuser:mypass@localhost:5432/butbul_halacha`

- **`YOUTUBE_API_KEY`**: YouTube Data API v3 key
  - How to get: Visit [Google Cloud Console](https://console.cloud.google.com/)
  - Enable the YouTube Data API v3
  - Create credentials (API Key)

- **`YOUTUBE_CHANNEL_ID`**: The YouTube channel ID to fetch videos from
  - For Harav Butbul's channel, find the channel ID from the channel URL
  - Format: Usually starts with `UC` followed by alphanumeric characters

## Using Configuration in Code

The configuration is centralized in `src/config.py` and can be imported throughout the application:

```python
from config import config

# Access configuration values
database_url = config.database_url
api_key = config.youtube_api_key
channel_id = config.youtube_channel_id
```

### Features

- **Type Safety**: Configuration values are typed for better IDE support
- **Validation**: Missing required variables raise clear errors on startup
- **Security**: Sensitive values are masked when printed/logged
- **Centralized**: Single source of truth for all configuration

## Example Usage

```python
from config import config
import psycopg2

# Connect to database
conn = psycopg2.connect(config.database_url)

# Use YouTube API
from googleapiclient.discovery import build

youtube = build('youtube', 'v3', developerKey=config.youtube_api_key)
```

## Testing

The configuration module includes comprehensive tests. Run them with:

```bash
poetry run pytest tests/test_config.py -v
```

## Security Notes

- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Configuration values are masked in logs and error messages
- Store production credentials securely (e.g., in a secrets manager)
