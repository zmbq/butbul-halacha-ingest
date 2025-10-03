# Pipeline Scripts

This directory contains the numbered pipeline scripts for processing YouTube videos.

## Pipeline Steps

### Step 01: Ingest Videos (`s01_ingest_videos.py`)
Fetches videos from YouTube playlists and stores them in both the database and JSON backup files.

**Usage:**
```bash
python -m src.pipeline.s01_ingest_videos
```

**What it does:**
- Finds playlists containing "הלכה יומית"
- Fetches all videos from those playlists
- Stores video metadata (ID, URL, title, description, published date)
- Saves to both PostgreSQL database and JSON backup
- Processes in batches of 100 for efficiency

### Step 02: Extract Metadata (`s02_extract_metadata.py`)
Extracts Hebrew dates, day of week, and subjects from video titles and descriptions.

**Usage:**
```bash
python -m src.pipeline.s02_extract_metadata
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
python -m src.pipeline.s01_ingest_videos

# Step 2: Extract metadata from video titles
python -m src.pipeline.s02_extract_metadata
```

## File Naming Convention

Files are named with a step prefix (`s01`, `s02`, etc.) to indicate the order they should be run in the pipeline. The "s" prefix stands for "step" and allows Python to import these modules easily while keeping the execution order clear in the filename.
