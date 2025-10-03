# butbul-halacha-ingest

Ingest and process data from Harav Butbul's הלכה יומית (Daily Halacha) YouTube videos.

## Project Overview

This project collects, processes, and stores metadata from Harav Aharon Butbul's daily Halacha videos on YouTube. The videos are organized in playlists by Hebrew year (תשפ"ב, תשפ"ג, תשפ"ד, etc.).

### Current Status

✅ **Step 1 Complete**: Video ingestion pipeline operational
- Successfully collected **1,123 videos** from 5 playlists
- Date range: February 2022 → October 2025
- Full metadata including descriptions and publish dates

## Setup

This project uses Poetry for dependency management and requires Python 3.12+.

### Prerequisites

- Python 3.12 or higher
- Poetry (install from https://python-poetry.org/docs/#installation)
- PostgreSQL database
- YouTube API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/zmbq/butbul-halacha-ingest.git
cd butbul-halacha-ingest
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file from the example:
```bash
cp .env.example .env
```

4. Edit `.env` and configure your settings:
   - `DATABASE_URL`: PostgreSQL connection string
   - `YOUTUBE_API_KEY`: Your YouTube Data API v3 key
   - `YOUTUBE_CHANNEL_ID`: The channel ID to ingest data from

### Usage

Run the complete ingestion pipeline:
```bash
poetry run python src/main.py
```

#### Individual Steps

**Step 1: Ingest Videos**
```bash
# Fetch videos from YouTube and store in database
poetry run python src/ingest_videos_v2.py

# View collection summary
poetry run python src/show_summary.py

# Import from JSON backup (if database was unavailable)
poetry run python src/import_from_json.py videos_backup.json
```

**Testing Components**
```bash
# Test YouTube API connectivity
poetry run python src/test_youtube.py

# Test database connectivity  
poetry run python src/test_db.py

# Run all tests
poetry run pytest
```

See [Step 1 Documentation](docs/STEP1_INGESTION.md) for detailed information.

### Development

This project includes the following development tools:
- `pytest`: Testing framework
- `black`: Code formatter
- `ruff`: Fast Python linter

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black src tests
```

Lint code:
```bash
poetry run ruff check src tests
```

## Project Structure

```
butbul-halacha-ingest/
├── src/                      # Source code
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models and connection
│   ├── youtube_service.py   # YouTube API client
│   ├── main.py              # Main entry point
│   ├── ingest_videos_v2.py  # Video ingestion with fallback
│   ├── import_from_json.py  # Import videos from JSON backup
│   ├── show_summary.py      # Display collection statistics
│   ├── test_youtube.py      # Test YouTube connectivity
│   └── test_db.py           # Test database connectivity
├── tests/                   # Test files
│   ├── test_config.py       # Configuration tests
│   └── test_main.py
├── docs/                    # Documentation
│   ├── CONFIGURATION.md     # Configuration guide
│   └── STEP1_INGESTION.md   # Step 1 documentation
├── .env                     # Environment variables (not in git)
├── .env.example             # Example environment configuration
├── videos_backup.json       # JSON backup of videos (if created)
├── pyproject.toml           # Poetry configuration and dependencies
└── README.md                # This file
```

## Pipeline Steps

### Step 1: Video Ingestion ✅

Collects videos from YouTube playlists containing "הלכה יומית":
- Fetches playlist information
- Retrieves all videos with metadata
- Stores in PostgreSQL database (or JSON fallback)
- Supports re-running without duplicates (upsert)

**Status**: Complete - 1,123 videos collected

### Step 2: Date Extraction (Planned)

Extract Hebrew and Gregorian dates from video descriptions:
- Parse Hebrew date formats (e.g., "ג' תשרי התשפ"ו")
- Extract topics and subjects
- Link videos to calendar dates

### Step 3: Content Analysis (Planned)

Process video content and metadata:
- Categorize by topic
- Extract key themes
- Build searchable index

## Dependencies

### Production
- `psycopg2-binary`: PostgreSQL adapter
- `sqlalchemy`: SQL toolkit and ORM
- `google-api-python-client`: YouTube Data API client
- `python-dotenv`: Load environment variables from .env file

### Development
- `pytest`: Testing framework
- `black`: Code formatter
- `ruff`: Python linter

## License

MIT License - see LICENSE file for details
