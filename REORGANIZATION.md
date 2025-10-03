# Project Reorganization - October 3, 2025

## Changes Made

### 1. Moved Test Files
All test files have been moved from `src/` to `tests/`:
- `src/test_day_of_week.py` → `tests/test_day_of_week.py`
- `src/test_extraction.py` → `tests/test_extraction.py`

### 2. Created Pipeline Directory
Created `src/pipeline/` directory to organize pipeline scripts in execution order:
- `src/ingest_videos.py` → `src/pipeline/ingest_videos_01.py`
- `src/extract_metadata.py` → `src/pipeline/extract_metadata_02.py`

### 3. Updated Imports
All imports have been updated to reflect the new structure:
- Pipeline scripts now use relative imports (`from ..database import ...`)
- Test files import from `src.pipeline.extract_metadata_02`
- Added `__init__.py` to `src/pipeline/` directory

## New Directory Structure

```
butbul-halacha-ingest/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── hebrew_date_utils.py
│   ├── main.py
│   ├── show_summary.py
│   ├── youtube_service.py
│   └── pipeline/
│       ├── __init__.py
│       ├── README.md
│       ├── ingest_videos_01.py          # Step 1: Fetch videos from YouTube
│       └── extract_metadata_02.py       # Step 2: Extract Hebrew dates & subjects
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_database.py
    ├── test_day_of_week.py             # Tests Hebrew date conversion
    ├── test_extraction.py              # Tests metadata extraction
    ├── test_main.py
    └── test_youtube_service.py
```

## Running Tests

Tests can now be run from the project root:

```bash
# Run individual test files
python -m tests.test_day_of_week
python -m tests.test_extraction

# Run all tests (future enhancement)
pytest tests/
```

## Running Pipeline Scripts

Pipeline scripts should be run in order:

```bash
# Step 1: Ingest videos
python -m src.pipeline.ingest_videos_01

# Step 2: Extract metadata
python -m src.pipeline.extract_metadata_02
```

## Benefits

1. **Clear Separation**: Tests are now in their own directory, separate from source code
2. **Ordered Pipeline**: Pipeline scripts are numbered, making execution order obvious
3. **Better Organization**: All pipeline logic is grouped together in `src/pipeline/`
4. **Easier to Extend**: Future pipeline steps (03, 04, etc.) can be added easily

## Verified Working

✅ All tests pass with new structure:
- `tests.test_day_of_week` - All 11 tests passing
- `tests.test_extraction` - All 3 tests passing

✅ Pipeline scripts are importable and executable:
- `src.pipeline.ingest_videos_01`
- `src.pipeline.extract_metadata_02`
