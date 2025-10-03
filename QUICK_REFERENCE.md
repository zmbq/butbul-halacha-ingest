# Quick Reference Guide

## Common Commands

### Setup
```bash
# Install dependencies
poetry install

# Create .env file from example
cp .env.example .env
# Then edit .env with your credentials

# Test configuration
poetry run python -c "from src.config import config; print(config)"
```

### Running the Pipeline

```bash
# Run complete pipeline (Step 1)
poetry run python src/main.py

# Run ingestion only
poetry run python src/ingest_videos_v2.py

# View collected videos summary
poetry run python src/show_summary.py
```

### Testing

```bash
# Test YouTube API
poetry run python src/test_youtube.py

# Test database connection
poetry run python src/test_db.py

# Run all unit tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v
```

### Database Operations

```bash
# Create database tables (using Python)
poetry run python -c "from src.database import init_db; init_db()"

# Import from JSON backup
poetry run python src/import_from_json.py videos_backup.json

# Or use SQL directly
psql -h your_host -U your_user -d your_db -f schema.sql
```

### Development

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Auto-fix linting issues
poetry run ruff check --fix src tests
```

## Quick Checks

### Is YouTube API working?
```bash
poetry run python src/test_youtube.py
```
Expected: List of playlists and videos

### Is database accessible?
```bash
poetry run python src/test_db.py
```
Expected: PostgreSQL version information

### How many videos collected?
```bash
poetry run python src/show_summary.py
```
Expected: Statistics and sample videos

## Environment Variables

Required in `.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_CHANNEL_ID=UCS9moGQA0U4MqWzT98mIlGw
```

## File Locations

| File | Location | Purpose |
|------|----------|---------|
| Configuration | `.env` | API keys and database URL |
| Video backup | `videos_backup.json` | JSON fallback when DB unavailable |
| Database schema | `schema.sql` | SQL to create tables |
| Main entry | `src/main.py` | Run complete pipeline |

## Troubleshooting

### "could not translate host name"
- Database connection issue
- Check internet connection
- Verify DATABASE_URL in `.env`
- Script will auto-save to JSON

### "YOUTUBE_API_KEY not set"
- Missing or invalid API key
- Check `.env` file exists
- Verify YOUTUBE_API_KEY is set

### "No videos found"
- Check YOUTUBE_CHANNEL_ID is correct
- Verify playlist filter matches playlist names
- Test with: `poetry run python src/test_youtube.py`

## Data Summary

Current collection (as of 2025-10-03):
- **Total Videos**: 1,123
- **Playlists**: 5 (תשפ"ב through תשפ"ו)
- **Date Range**: Feb 2022 - Oct 2025
- **Storage**: JSON backup (database pending connectivity)

## Next Steps

1. ✅ Video ingestion complete
2. 📋 Parse Hebrew dates from descriptions
3. 📋 Extract topics and themes
4. 📋 Build search interface
