# Day of Week Extraction Feature

## ✅ Completed

### 1. Database Schema Update
- Added `day_of_week` column to `video_metadata` table
- Migration: `alembic/versions/5cdf4eb091b7_add_day_of_week_to_video_metadata.py`
- Applied successfully with `poetry run alembic upgrade head`

### 2. Hebrew Date Utilities
Created `src/hebrew_date_utils.py` with functions:
- `extract_day_of_week(hebrew_date)` - Extracts day abbreviation (e.g., "ג'", "ד'")
- `get_day_name(day_abbreviation)` - Converts abbreviation to full name (e.g., "שלישי", "רביעי")
- `parse_hebrew_date(hebrew_date)` - Full parser (returns dict with all components)

### 3. Day of Week Mappings
```python
HEBREW_DAYS = {
    "א'": "ראשון",      # Sunday
    "ב'": "שני",        # Monday
    "ג'": "שלישי",      # Tuesday
    "ד'": "רביעי",      # Wednesday
    "ה'": "חמישי",      # Thursday
    "ו'": "שישי",       # Friday
    "ש'": "שבת",        # Saturday (abbreviated)
    "שבת": "שבת",       # Saturday (full word)
}
```

### 4. Updated Extraction Script
Modified `src/extract_metadata.py` to:
- Import `extract_day_of_week` from `hebrew_date_utils`
- Extract day of week from Hebrew dates
- Store in `video_metadata.day_of_week` column
- Display day of week in sample output

### 5. Comprehensive Testing
Created `src/test_day_of_week.py` with:
- 11 test cases for various Hebrew date formats
- Tests for all days of the week (Sunday-Saturday)
- Edge cases (no day of week, empty strings, None values)
- Real-world examples from actual video data
- All tests passing ✓

## Example Extraction

### Input
```
Title: "הגאון הרב אהרון בוטבול - הלכה יומית - ג' תשרי התשפ"ו - יום כנגד שנה: כוחם של עשרת ימי תשובה"
```

### Extracted Metadata
```python
{
    "video_id": "YChnKwkxujI",
    "hebrew_date": "ג' תשרי התשפ\"ו",
    "day_of_week": "ג'",          # NEW!
    "subject": "יום כנגד שנה: כוחם של עשרת ימי תשובה"
}
```

### Full Day Name
Using `get_day_name("ג'")` returns `"שלישי"` (Tuesday)

## How It Works

### Pattern Recognition
The `extract_day_of_week()` function looks for:
1. Single Hebrew letter at the start of the date
2. Followed by an apostrophe (') and space
3. Must be one of the valid day letters: א, ב, ג, ד, ה, ו, ש

### Examples That Match
- "ג' תשרי התשפ\"ו" → "ג'" (Tuesday)
- "ד' תשרי התשפ\"ו" → "ד'" (Wednesday)
- "שבת פרשת נח" → "שבת" (Saturday)

### Examples That Don't Match
- "י\"א תשרי התשפ\"ו" → None (starts with day number, not day of week)
- "כ\"ה כסלו התשפ\"ו" → None (no day of week prefix)

## Testing

### Run Day of Week Tests
```bash
python -m src.test_day_of_week
```

Output shows all 11 tests passing:
- Tests for all 7 days of week
- Edge cases (no day, empty, None)
- Real-world video examples

### Run Extraction Tests
```bash
python -m src.test_extraction
```

Verifies that the full extraction pipeline (including day of week) works correctly.

## Database Schema

### video_metadata Table (Updated)
```sql
CREATE TABLE video_metadata (
    video_id VARCHAR(20) PRIMARY KEY,
    hebrew_date VARCHAR(50),
    day_of_week VARCHAR(20),      -- NEW COLUMN
    subject VARCHAR(500),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

## Next Steps

Ready to run the extraction:
```bash
# 1. Ensure videos are ingested
python -m src.ingest_videos

# 2. Extract metadata (including day of week)
python -m src.extract_metadata
```

The extraction script will now populate the `day_of_week` field automatically!

## Migration History

```bash
poetry run alembic history
```

Shows:
1. `4d9669060f11` - Initial migration with video table
2. `d4912baf41f5` - Add video_metadata table
3. `5cdf4eb091b7` - Add day_of_week to video_metadata (current)
