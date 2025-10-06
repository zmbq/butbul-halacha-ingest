"""Pipeline step: tag videos by Hebrew year found in `video_metadata.hebrew_date`.

This script will:
  - Delete all existing taggings (intentional full re-tag run)
  - Scan `video_metadata.hebrew_date` for year tokens using a regex
  - Create `Tag` rows for each discovered year (type='date')
  - Create `Tagging` rows linking videos to their year tag

Note: running this will modify the database. Use in a dev environment first.
"""
import re
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import select
from typing import cast
from src.database import SessionLocal, Tag, Tagging, VideoMetadata

# Regex to capture Hebrew year tokens at end of string like: '... התשפ"ו' or '... התשפא' etc.
# We look for the word התשפ plus up to 2 Hebrew letters or punctuation at the end.
HEBREW_YEAR_RE = re.compile(r"(התשפ[\u05D0-\u05EA\"']{0,2})$")


def extract_year_token(hebrew_date: str) -> str | None:
    if not hebrew_date:
        return None
    m = HEBREW_YEAR_RE.search(hebrew_date.strip())
    if not m:
        return None
    return m.group(1)


def get_or_create_year_tag(db, year: str, cache: dict[str, int]) -> int:
    """Return tag id for `year`, creating a Tag row if necessary and updating cache.

    `db` is a SQLAlchemy session. `cache` maps year->tag_id and is mutated.
    """
    if year in cache:
        return cache[year]

    existing = db.execute(select(Tag).where(Tag.name == year)).scalars().first()
    if existing:
        tag_id = cast(int, existing.id)
    else:
        tag = Tag(name=year, description=f'Year tag for {year}', type='date')
        db.add(tag)
        db.flush()
        tag_id = cast(int, tag.id)

    cache[year] = tag_id
    return tag_id


def run() -> None:
    """Run the tagging pipeline step.

    Behavior:
      - Delete all rows from `taggings` (full re-tag)
      - Load existing year tags into a cache
      - Ensure `tags` rows exist for each found year (type='date')
      - Insert `taggings` linking videos to the year tag
    """
    db = SessionLocal()
    try:
        # remove existing taggings
        db.execute(sa.text('DELETE FROM taggings'))
        db.commit()


        # Process year tags (separated for incremental development and testing)
        process_year_tags(db)

        db.commit()
    finally:
        db.close()


def process_year_tags(db) -> None:
    """Scan video metadata for year tokens and create taggings accordingly."""
    # preload year tags into cache
    cache: dict[str, int] = {}
    rows = db.execute(select(Tag.name, Tag.id).where(Tag.type == 'date')).all()
    for name, tid in rows:
        cache[name] = cast(int, tid)

    # scan all video metadata rows
    rows = db.execute(select(VideoMetadata.video_id, VideoMetadata.hebrew_date)).all()
    for video_id, hebrew_date in rows:
        year = extract_year_token(hebrew_date if hebrew_date is not None else '')
        if not year:
            continue

        tag_id = get_or_create_year_tag(db, year, cache)
        tagging = Tagging(tag_id=tag_id, video_id=video_id, source='year-extract')
        db.add(tagging)


if __name__ == '__main__':
    print('Starting tag_videos pipeline step (year tags) at', datetime.now(timezone.utc).isoformat())
    run()
    print('Finished tagging')
