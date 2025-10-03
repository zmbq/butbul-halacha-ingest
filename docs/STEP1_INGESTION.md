# Step 1: Video Ingestion Pipeline

## Overview

Step 1 of the pipeline fetches all הלכה יומית (Daily Halacha) videos from Harav Butbul's YouTube channel and stores them in a database.

## What It Does

1. **Searches YouTube**: Finds all playlists containing "הלכה יומית" in their name
2. **Fetches Videos**: Retrieves all videos from matching playlists
3. **Stores Metadata**: Saves video information to PostgreSQL database
4. **Handles Updates**: Re-running updates existing records without duplication (upsert)

## Database Schema

The `videos` table contains:

| Column | Type | Description |
|--------|------|-------------|
| `video_id` | VARCHAR(20) | YouTube video ID (Primary Key) |
| `url` | VARCHAR(255) | Full YouTube video URL |
| `description` | TEXT | Video description from YouTube |
| `published_at` | TIMESTAMP | Video publish date (from YouTube) |
| `created_at` | TIMESTAMP | Record creation timestamp |
| `updated_at` | TIMESTAMP | Record last update timestamp |

## Usage

### Running the Ingestion

```bash
# Run the complete pipeline
poetry run python src/main.py

# Or run step 1 directly
poetry run python src/ingest_videos_v2.py
```

### Testing Components

```bash
# Test YouTube API connectivity
poetry run python src/test_youtube.py

# Test database connectivity
poetry run python src/test_db.py

# Show summary of collected videos
poetry run python src/show_summary.py
```

## Current Status (2025-10-03)

✅ **Successfully collected 1,123 videos** from 5 playlists:

- **תשפ"ו (5786)**: 7 videos
- **תשפ"ה (5785)**: 294 videos  
- **תשפ"ד (5784)**: 320 videos
- **תשפ"ג (5783)**: 298 videos
- **תשפ"ב (5782)**: 199 videos

**Date Range**: February 6, 2022 → October 2, 2025

## Fallback Mode

If the database is unavailable, the script automatically:
1. Saves all videos to `videos_backup.json`
2. Provides instructions for importing later

### Importing from JSON

When the database becomes available:

```bash
poetry run python src/import_from_json.py videos_backup.json
```

## Features

### Intelligent Upsert
- Uses PostgreSQL's `ON CONFLICT` for efficient upsert operations
- Updates changed records without creating duplicates
- Preserves `created_at` timestamp on updates

### Error Handling
- Gracefully handles database connection failures
- Falls back to JSON storage when needed
- Provides detailed progress and error reporting

### Progress Tracking
- Shows real-time progress during ingestion
- Displays counts of successful/failed operations
- Provides summary statistics at completion

## Scripts Overview

| Script | Purpose |
|--------|---------|
| `database.py` | SQLAlchemy models and database connection |
| `youtube_service.py` | YouTube API client for fetching videos |
| `ingest_videos_v2.py` | Main ingestion script with fallback |
| `import_from_json.py` | Import videos from JSON to database |
| `show_summary.py` | Display collection statistics |
| `test_youtube.py` | Test YouTube API connectivity |
| `test_db.py` | Test database connectivity |

## Next Steps

After Step 1 is complete, the next steps would be:

1. **Parse Dates**: Extract Hebrew dates from video descriptions
2. **Content Analysis**: Analyze topics and themes
3. **Search Integration**: Build search and discovery features
4. **Web Interface**: Create UI for browsing videos

## Troubleshooting

### Database Connection Issues

If you see: `could not translate host name`

**Solutions:**
1. Check your internet connection
2. Verify the DATABASE_URL in `.env` is correct
3. Check if firewall is blocking the connection
4. Use the JSON fallback (automatic) and import later

### YouTube API Issues

If you see: `HttpError` or quota errors

**Solutions:**
1. Verify YOUTUBE_API_KEY in `.env` is valid
2. Check API quota in Google Cloud Console
3. Wait for quota reset (happens daily)

### Import Errors

If importing from JSON fails:

**Solutions:**
1. Verify database is accessible first
2. Check JSON file exists and is valid
3. Ensure table schema is created (`init_db()`)
