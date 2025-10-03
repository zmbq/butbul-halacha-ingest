# butbul-halacha-ingest

Ingest the data for the butbul halacha yomit project

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

Run the ingestion script:
```bash
poetry run python src/main.py
```

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
├── src/               # Source code
│   ├── __init__.py
│   └── main.py       # Main entry point
├── tests/            # Test files
├── .env.example      # Example environment configuration
├── pyproject.toml    # Poetry configuration and dependencies
└── README.md         # This file
```

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
