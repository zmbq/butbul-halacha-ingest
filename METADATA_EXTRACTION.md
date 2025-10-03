# Video Metadata Extraction

This document explains the video metadata extraction process.

## Overview

The ingestion pipeline has two main phases:
1. **Video Ingestion** (`src/ingest_videos.py`) - Fetches videos from YouTube and stores them in the `videos` table
2. **Metadata Extraction** (`src/extract_metadata.py`) - Extracts Hebrew dates and subjects from video titles/descriptions and stores them in the `video_metadata` table

## Database Schema

### videos table
- `video_id` (PK) - YouTube video ID
- `url` - Full YouTube URL
- `title` - Video title from YouTube
- `description` - Video description from YouTube
- `published_at` - Publication date
- `created_at`, `updated_at` - Record timestamps

### video_metadata table
- `video_id` (PK, FK) - Links to videos table
- `hebrew_date` - Extracted Hebrew date (e.g., "ג' תשרי התשפ\"ו")
- `subject` - Extracted subject/topic
- `created_at`, `updated_at` - Record timestamps

## Data Format Patterns

### Title Format
```
הגאון הרב אהרון בוטבול - הלכה יומית - [Hebrew Date] - [Subject]
```

**Example:**
```
הגאון הרב אהרון בוטבול - הלכה יומית - ג' תשרי התשפ"ו - יום כנגד שנה: כוחם של עשרת ימי תשובה
```

### Description Format
```
הלכה יומית - [Hebrew Date] - [Subject]

[WhatsApp group invitation text]
```

**Example:**
```
הלכה יומית - ג' תשרי התשפ"ו - יום כנגד שנה: כוחם של עשרת ימי תשובה

להצטרפות לקבוצת הוואטסאפ לקבלת עדכונים (קבוצה שקטה, עדכונים בנושא הרב שליט"א בלבד):
https://chat.whatsapp.com/G7SsJQ5dR3MLc84P8nP71C
```

## Running the Pipeline

### Step 1: Ingest Videos from YouTube

```bash
python -m src.ingest_videos
```

This will:
- Fetch all videos from playlists containing "הלכה יומית"
- Save to JSON backup (`data/videos_backup.json`)
- Store in database (`videos` table)

### Step 2: Extract Metadata

```bash
python -m src.extract_metadata
```

This will:
- Read all videos from the `videos` table
- Parse Hebrew dates and subjects from titles/descriptions
- Store extracted metadata in `video_metadata` table
- Process in batches of 100 for efficiency

## Extraction Logic

The `extract_hebrew_date_and_subject()` function:

1. Removes WhatsApp invitation text from descriptions
2. Strips the "הגאון הרב אהרון בוטבול - " prefix if present
3. Expects format: "הלכה יומית - [date] - [subject]"
4. Splits on " - " delimiter to extract date and subject
5. Returns tuple of (hebrew_date, subject)

**Fallback:** If extraction from title fails, it tries the description.

## Example Extraction Results

| Video ID | Hebrew Date | Subject |
|----------|-------------|---------|
| YChnKwkxujI | ג' תשרי התשפ"ו | יום כנגד שנה: כוחם של עשרת ימי תשובה |
| 3pCxWIdvpFA | ד' תשרי התשפ"ו | גדולה שבת שמסלקת את היסורים |
| y-41Vo9LeRo | ו' תשרי התשפ"ו | כח התורה והחסד לבטל גזירת הייסורים |

## Testing Extraction Logic

To test the extraction logic without touching the database:

```bash
python -m src.test_extraction
```

This runs unit tests with sample data to verify the parsing works correctly.

## Database Migration

The `video_metadata` table was added using Alembic migrations:

```bash
# Migration was created with:
poetry run alembic revision --autogenerate -m "Add video_metadata table"

# Applied with:
poetry run alembic upgrade head
```

See [MIGRATIONS.md](MIGRATIONS.md) for more information about database migrations.

## Batch Processing

Both scripts use batch processing (100 records at a time) for efficiency:
- Reduces database round trips
- Faster execution
- Better error handling

## Error Handling

- **Extraction errors**: If Hebrew date cannot be extracted, the record is still created with NULL values
- **Database errors**: Batch operations use transactions - if a batch fails, it's rolled back
- **Progress tracking**: Console output shows success/error counts for monitoring

## Re-running Extraction

The extraction script can be run multiple times safely:
- Uses upsert logic (INSERT ... ON CONFLICT DO UPDATE)
- Updates existing records if found
- Idempotent - safe to re-run

## Next Steps

After extraction, you can:
1. Query videos by Hebrew date
2. Search by subject
3. Build analysis on topics and dates
4. Convert Hebrew dates to Gregorian dates (future enhancement)
