# Project Structure

Clean, organized structure for the Butbul Halacha video ingestion project.

## Directory Layout

```
butbul-halacha-ingest/
├── src/                          # Source code
│   ├── config.py                 # Configuration management
│   ├── database.py               # SQLAlchemy models
│   ├── hebrew_date_utils.py      # Hebrew date parsing & conversion
│   ├── main.py                   # Main entry point
│   ├── show_summary.py           # Database summary display
│   ├── youtube_service.py        # YouTube API wrapper
│   └── pipeline/                 # Numbered pipeline steps
│       ├── s01_ingest_videos.py      # Step 1: Fetch from YouTube
│       └── s02_extract_metadata.py   # Step 2: Extract Hebrew dates
│
├── tests/                        # All test files
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_day_of_week.py      # Hebrew date conversion tests
│   ├── test_extraction.py       # Metadata extraction tests
│   ├── test_main.py
│   └── test_youtube_service.py
│
├── agent-summaries/              # AI-generated documentation
│   ├── DAY_OF_WEEK_FEATURE.md
│   ├── METADATA_EXTRACTION.md
│   ├── MIGRATIONS.md
│   ├── PIPELINE.md
│   └── REORGANIZATION.md
│
├── alembic/                      # Database migrations
├── data/                         # JSON backups
└── env/                          # Python virtual environment
```

## Running the Project

### Run Tests
```bash
python -m tests.test_day_of_week
python -m tests.test_extraction
```

### Run Pipeline
```bash
# Step 1: Ingest videos from YouTube
python -m src.pipeline.s01_ingest_videos

# Step 2: Extract metadata from titles
python -m src.pipeline.s02_extract_metadata
```

## Key Features

- **Numbered Pipeline**: Steps prefixed with `s01`, `s02` for clear execution order
- **Separated Concerns**: Tests in `tests/`, docs in `agent-summaries/`, code in `src/`
- **Hebrew Date Handling**: Full Hebrew-to-Gregorian conversion with day of week calculation
- **Batch Processing**: 100 records per transaction for efficiency
- **Dual Storage**: Database + JSON backup for safety
- **Migration System**: Alembic for version-controlled schema changes
