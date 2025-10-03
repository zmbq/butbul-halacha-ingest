# Pipeline Scripts

This directory contains the numbered pipeline scripts for processing YouTube videos.

## Pipeline Steps

### 01. Ingest Videos (`ingest_videos_01.py`)
Fetches videos from YouTube playlists and stores them in both the database and JSON backup files.

**Usage:**
```bash
python -m src.pipeline.ingest_videos_01
```

**What it does:**
- Finds playlists containing "הלכה יומית"
- Fetches all videos from those playlists
- Stores video metadata (ID, URL, title, description, published date)
- Saves to both PostgreSQL database and JSON backup
- Processes in batches of 100 for efficiency

### 02. Extract Metadata (`extract_metadata_02.py`)
Extracts Hebrew dates, day of week, and subjects from video titles and descriptions.

**Usage:**
```bash
python -m src.pipeline.extract_metadata_02
```

**What it does:**
- Parses Hebrew dates from video titles/descriptions
- Converts Hebrew dates to Gregorian dates using pyluach
- Calculates the day of week from the Gregorian date
- Extracts the subject/topic from the title
- Stores metadata in the video_metadata table
- Processes in batches of 100 for efficiency

## Running the Full Pipeline

To run the complete pipeline from scratch:

```bash
# Step 1: Ingest videos from YouTube
python -m src.pipeline.ingest_videos_01

# Step 2: Extract metadata from video titles
python -m src.pipeline.extract_metadata_02
```

## File Naming Convention

Files are named with a two-digit prefix (01, 02, etc.) to indicate the order they should be run in the pipeline. The number is placed at the end of the filename (e.g., `ingest_videos_01.py`) to make Python imports easier.
