"""s07: Pipeline step — tag videos by Hebrew year found in `video_metadata.hebrew_date`.

This script will:
  - Delete all existing taggings (intentional full re-tag run)
  - Scan `video_metadata.hebrew_date` for year tokens using a regex
  - Create `Tag` rows for each discovered year (type='date')
  - Create `Tagging` rows linking videos to their year tag

Note: running this will modify the database. Use in a dev environment first.
"""
STEP = 7

import re
from datetime import datetime, timezone
import sqlalchemy as sa
from sqlalchemy import select
from dataclasses import dataclass, field
from typing import cast, List
from src.database import SessionLocal, Tag, Tagging, VideoMetadata

# Manual tags configuration as typed dataclasses: name and list of search terms (OR)


@dataclass(frozen=True)
class ManualTag:
    name: str
    terms: List[str] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)


MANUAL_TAGS: List[ManualTag] = [
    ManualTag(name="פרשת השבוע", terms=["פרשת"]),
    ManualTag(name="שבת", terms=["שבת"]),
    ManualTag(name="ראש חודש", terms=["ראש חודש"]),
    # Separate holiday tags for מועדי ישראל
    ManualTag(name="ראש השנה", terms=["ראש השנה"]),
    ManualTag(name="יום כיפור", terms=["כיפור"]),
    ManualTag(name="סוכות", terms=["סוכות", "סוכה"]),
    ManualTag(name="פסח", terms=["פסח", "חמץ", "מצה"]),
    ManualTag(name="שבועות", terms=["שבועות"]),
    # Additional holidays
    ManualTag(name="חנוכה", terms=["חנוכה", "חנוכיה"]),
    # פורים: ensure we don't match כיפור; add exclude list to avoid false positives
    ManualTag(name="פורים", terms=["פורים"], exclude=["כיפור"]),
    ManualTag(name="כשרות", terms=["חלבי", "בשרי", "פרווה"]),
    ManualTag(name="תענית", terms=["תענית", "צום"]),
    ManualTag(name="ברכות", terms=["ברכות", "ברכה", "ברכת"])
]

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


def process_year_tags(db) -> None:
    """Scan video metadata for year tokens and create taggings accordingly."""
    # preload year tags into cache
    cache: dict[str, int] = {}
    rows = db.execute(select(Tag.name, Tag.id).where(Tag.type == 'date')).all()
    for name, tid in rows:
        cache[name] = cast(int, tid)

    # scan all video metadata rows
    rows = db.execute(select(VideoMetadata.video_id, VideoMetadata.hebrew_date)).all()
    total = len(rows)
    created_tags = 0
    created_taggings = 0
    scanned = 0
    progress_interval = max(1, total // 20)

    for video_id, hebrew_date in rows:
        scanned += 1
        year = extract_year_token(hebrew_date if hebrew_date is not None else '')
        if not year:
            if scanned % progress_interval == 0:
                print(f's07: scanned {scanned}/{total} rows, tags so far: {len(cache)}, taggings so far: {created_taggings}')
            continue

        # detect whether get_or_create created a new tag by checking cache membership
        existed_before = year in cache
        tag_id = get_or_create_year_tag(db, year, cache)
        if not existed_before:
            created_tags += 1

        tagging = Tagging(tag_id=tag_id, video_id=video_id, source='year-extract')
        db.add(tagging)
        created_taggings += 1

        if scanned % progress_interval == 0:
            print(f's07: scanned {scanned}/{total} rows, tags so far: {len(cache)}, taggings so far: {created_taggings}')

    print(f's07: finished scanning. total={total}, created_tags={created_tags}, created_taggings={created_taggings}')


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

        # Process manual tags (parsha, שבת, ראש חודש, מועדי ישראל, ...)
        process_manual_tags(db)

        db.commit()
    finally:
        db.close()


def process_manual_tags(db) -> None:
    """Process all manual tags defined in MANUAL_TAGS.

    For each entry in MANUAL_TAGS (name + list of terms), ensure the Tag exists
    and create Tagging rows for videos whose subject matches any of the terms
    (DB-side ILIKE across ORed terms).
    """
    for entry in MANUAL_TAGS:
        name = entry.name
        terms = entry.terms or []
        if not terms:
            continue

        # ensure tag exists
        existing = db.execute(select(Tag).where(Tag.name == name)).scalars().first()
        if existing:
            tag_id = cast(int, existing.id)
        else:
            tag = Tag(name=name, description=f'Manual tag {name}', type='manual')
            db.add(tag)
            db.flush()
            tag_id = cast(int, tag.id)

        # build ORed ILIKE expressions for the search terms
        ilike_clauses = [VideoMetadata.subject.ilike(f'%{t}%') for t in terms]
        where_clause = sa.or_(*ilike_clauses)

        # handle optional excludes
        excludes = entry.exclude or []
        if excludes:
            not_clauses = [~VideoMetadata.subject.ilike(f'%{e}%') for e in excludes]
            where_clause = sa.and_(where_clause, sa.and_(*not_clauses))

        rows = db.execute(select(VideoMetadata.video_id).where(where_clause)).all()
        total = len(rows)
        created = 0
        for i, (video_id,) in enumerate(rows, start=1):
            db.add(Tagging(tag_id=tag_id, video_id=video_id, source=f'manual-{name}'))
            created += 1
            if i % max(1, total // 10) == 0:
                print(f's07-manual: tag="{name}" tagged {i}/{total} videos so far')

        print(f's07-manual: finished tagging for "{name}". total_tagged={created}')


if __name__ == '__main__':
    print('Starting s07_tag_videos pipeline step (year tags) at', datetime.now(timezone.utc).isoformat())
    run()
    print('Finished tagging')
