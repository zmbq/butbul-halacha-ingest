# Project Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Butbul Halacha Ingest System                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   YouTube API    │
│  (Google Cloud)  │
└────────┬─────────┘
         │
         │ API Key
         │ Channel ID
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        YouTubeService                               │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ • get_playlists(filter="הלכה יומית")                      │   │
│  │ • get_playlist_videos(playlist_id)                         │   │
│  │ • get_videos_from_filtered_playlists()                     │   │
│  └────────────────────────────────────────────────────────────┘   │
└────────┬────────────────────────────────────────────────────────────┘
         │
         │ Video metadata (1,123 videos)
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Ingestion Pipeline                              │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 1. Fetch playlists with "הלכה יומית"                     │   │
│  │ 2. Extract all videos from playlists                       │   │
│  │ 3. Attempt database storage (upsert)                       │   │
│  │ 4. Fallback to JSON if DB unavailable                      │   │
│  └────────────────────────────────────────────────────────────┘   │
└────┬───────────────────────────────────────────────────────┬────────┘
     │                                                       │
     │ Database Available                                    │ Database Unavailable
     ▼                                                       ▼
┌──────────────────────┐                        ┌────────────────────────┐
│  PostgreSQL Database │                        │   videos_backup.json   │
│   (Supabase)         │                        │      (0.71 MB)         │
│                      │                        │                        │
│  ┌────────────────┐  │                        │  1,123 videos          │
│  │  videos table  │  │                        │  Ready for import      │
│  │                │  │                        └────────┬───────────────┘
│  │ • video_id PK  │  │                                 │
│  │ • url          │  │                                 │ When DB available
│  │ • description  │  │                                 │
│  │ • published_at │  │                                 ▼
│  │ • created_at   │  │                        ┌────────────────────────┐
│  │ • updated_at   │  │◄───────────────────────│  import_from_json.py   │
│  └────────────────┘  │                        └────────────────────────┘
└──────────────────────┘
```

## Data Flow

```
Step 1: Collection
──────────────────

YouTube Channel
  │
  ├── Playlist: הלכה יומית תשפ"ו (7 videos)
  ├── Playlist: הלכה יומית תשפ"ה (294 videos)
  ├── Playlist: הלכה יומית תשפ"ד (320 videos)
  ├── Playlist: הלכה יומית תשפ"ג (298 videos)
  └── Playlist: הלכה יומית תשפ"ב (199 videos)
           │
           ▼
    YouTubeService
           │
           ▼
    [1,123 Videos]
           │
           ├──────────────────┬──────────────────┐
           ▼                  ▼                  ▼
      video_id            url            description
      published_at        title          ...
```

## Component Interaction

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   main.py   │────────▶│  config.py   │◀────────│   .env      │
└──────┬──────┘         └──────────────┘         └─────────────┘
       │                                                │
       │                                                │
       │ imports                               Database URL
       │                                       YouTube API Key
       ▼                                       Channel ID
┌────────────────────┐
│ ingest_videos_v2   │
└─────┬──────────────┘
      │
      │ uses
      ├──────────────────────────┬─────────────────────────┐
      ▼                          ▼                         ▼
┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ youtube_service│    │   database.py    │    │  JSON backup     │
└────────────────┘    └──────────────────┘    └──────────────────┘
      │                         │                        │
      │                         │                        │
      ▼                         ▼                        ▼
┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ YouTube API v3 │    │   PostgreSQL     │    │ videos_backup    │
│ (Google)       │    │   (Supabase)     │    │     .json        │
└────────────────┘    └──────────────────┘    └──────────────────┘
```

## File Structure Tree

```
butbul-halacha-ingest/
│
├── 📁 src/                          # Source code
│   ├── 🐍 __init__.py              # Package initialization
│   ├── ⚙️  config.py                # Configuration from .env
│   ├── 🗄️  database.py              # SQLAlchemy models
│   ├── 📹 youtube_service.py        # YouTube API client
│   ├── 🚀 main.py                   # Application entry point
│   ├── 📥 ingest_videos_v2.py       # Main ingestion pipeline
│   ├── 💾 import_from_json.py       # JSON → Database importer
│   ├── 📊 show_summary.py           # Statistics display
│   ├── 🧪 test_youtube.py           # YouTube API test
│   └── 🧪 test_db.py                # Database test
│
├── 📁 tests/                        # Unit tests
│   ├── 🐍 __init__.py
│   ├── ✅ test_config.py            # Config tests (3/3 passing)
│   └── ✅ test_main.py
│
├── 📁 docs/                         # Documentation
│   ├── 📄 CONFIGURATION.md          # Setup guide
│   └── 📄 STEP1_INGESTION.md        # Pipeline documentation
│
├── 📁 env/                          # Python virtual environment
│
├── 🔒 .env                          # Environment variables (secret)
├── 📋 .env.example                  # Template for .env
├── 🚫 .gitignore                    # Git ignore rules
├── 📜 schema.sql                    # Database schema SQL
├── 📦 pyproject.toml                # Poetry dependencies
├── 🔒 poetry.lock                   # Locked dependencies
├── 📖 README.md                     # Project overview
├── 📝 QUICK_REFERENCE.md            # Command reference
├── 📋 IMPLEMENTATION_SUMMARY.md     # This summary
└── 💾 videos_backup.json            # Collected videos (0.71 MB)
```

## Module Dependencies

```
main.py
  └── config.py
        └── python-dotenv
              └── .env

  └── ingest_videos_v2.py
        ├── config.py
        ├── database.py
        │     ├── sqlalchemy
        │     ├── psycopg2-binary
        │     └── config.py
        └── youtube_service.py
              ├── google-api-python-client
              └── config.py
```

## Execution Flow

```
1. User runs: poetry run python src/main.py
                      │
                      ▼
2. main.py loads config from .env
                      │
                      ▼
3. Calls ingest_videos("הלכה יומית")
                      │
                      ▼
4. YouTubeService connects to API
                      │
                      ▼
5. Fetches playlists matching filter
                      │
                      ▼
6. For each playlist: fetch all videos
                      │
                      ▼
7. Try database connection
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
    SUCCESS                    FAILURE
         │                         │
         ▼                         ▼
8a. Upsert to DB            8b. Save to JSON
         │                         │
         ▼                         ▼
9a. Show DB summary         9b. Show JSON path
                                  │
                                  ▼
                           9c. Show import command
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│          Application Layer              │
│  • Python 3.12+                         │
│  • Poetry (dependency management)       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│          Framework Layer                │
│  • SQLAlchemy 2.0 (ORM)                 │
│  • Google API Client (YouTube)          │
│  • python-dotenv (config)               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│          Infrastructure Layer           │
│  • PostgreSQL (Supabase)                │
│  • YouTube Data API v3                  │
│  • JSON (fallback storage)              │
└─────────────────────────────────────────┘
```

## Error Handling Flow

```
Try: Connect to Database
  │
  ├─ Success ──────────────────────────────┐
  │                                        │
  │  Try: Upsert videos                   │
  │    │                                   │
  │    ├─ Success ──▶ Continue            │
  │    │                                   │
  │    └─ Error ───▶ Log error            │
  │                  Rollback              │
  │                  Continue with next    │
  │                                        │
  └─ Database connection failure           │
       │                                   │
       └──▶ Fallback to JSON               │
              │                            │
              └──▶ Save all videos         │
                   Generate import cmd     │
                                           │
  ┌────────────────────────────────────────┘
  │
  └──▶ Display summary statistics
       Exit gracefully
```

This architecture ensures:
- ✅ Modularity: Each component has single responsibility
- ✅ Testability: Components can be tested independently  
- ✅ Resilience: Fallback mechanisms prevent data loss
- ✅ Maintainability: Clear separation of concerns
- ✅ Scalability: Easy to add new pipeline steps
