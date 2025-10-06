"""
Populate transcription_segments table - Step 4 of the pipeline.

This script reads the `segments` field from the `transcripts` table (JSONB produced by
Whisper) and inserts each segment as a row into `transcription_segments` for easier
embedding generation and time-based queries.

Usage:
    python -m src.pipeline.s04_populate_transcription_segments --limit 100

By default it processes all transcripts that have segments and inserts missing segment
rows. It will avoid duplicates by checking for existing (video_id, source, segment_index).
"""

from datetime import datetime, timezone
from pathlib import Path
import json
import sys
from sqlalchemy import select, and_, text
from sqlalchemy.dialects.postgresql import insert
import sqlalchemy as sa
from ..database import get_db, init_db, TranscriptionSegment, Transcript, engine
from ..config import config


def populate_segments(limit: int | None = None, dry_run: bool = False, clear_flag: bool = False):
    print("=" * 80)
    print("Populate transcription_segments - Step 4")
    print("=" * 80)

    init_db()
    db = get_db()

    try:
        # Select transcripts that have segments
        stmt = select(Transcript).where(Transcript.segments.isnot(None))
        if limit:
            stmt = stmt.limit(limit)

        transcripts = db.execute(stmt).scalars().all()

        total = len(transcripts)
        print(f"Found {total} transcripts with segments to process")

        inserted = 0
        skipped = 0

        for t_idx, transcript in enumerate(transcripts, start=1):
            video_id = transcript.video_id
            source = transcript.source

            # Normalize segments into a Python list safely
            raw_segments = transcript.segments
            if raw_segments is None:
                segments = []
            elif isinstance(raw_segments, list):
                segments = raw_segments
            else:
                try:
                    segments = list(raw_segments)
                except Exception:
                    # Fallback: wrap single item
                    segments = [raw_segments]

            rows_to_insert = []
            for idx, seg in enumerate(segments):
                # Normalize fields
                if not isinstance(seg, dict):
                    # If malformed, skip
                    skipped += 1
                    continue

                seg_text = seg.get('text', '').strip()
                seg_start = float(seg.get('start', 0.0))
                seg_duration = float(seg.get('duration', 0.0))
                seg_end = seg_start + seg_duration

                # Prepare row for bulk insert
                now = datetime.now(timezone.utc)
                row = {
                    'video_id': video_id,
                    'source': source,
                    'segment_index': idx,
                    'start': seg_start,
                    'duration': seg_duration,
                    'end': seg_end,
                    'text': seg_text,
                    'raw': seg,
                    'created_at': now,
                    'updated_at': now,
                }

                if dry_run:
                    print(f"DRY: would insert {video_id} idx={idx} start={seg_start} len={len(seg_text)}")
                    inserted += 1
                    continue

                rows_to_insert.append(row)

            # Perform one transaction per transcription.
            if rows_to_insert:
                try:
                    # Begin a transactional block on this session/connection
                    # If clear flag was passed at top-level, remove existing segments for this video first
                    if clear_flag and not dry_run:
                        del_stmt = (
                            sa.delete(TranscriptionSegment)
                            .where(
                                and_(
                                    TranscriptionSegment.video_id == video_id,
                                    TranscriptionSegment.source == source,
                                )
                            )
                        )
                        db.execute(del_stmt)

                    if dry_run:
                        # For dry-run we already printed insert messages above
                        inserted += len(rows_to_insert)
                    else:
                        # Single bulk upsert for all rows of this transcription
                        stmt = insert(TranscriptionSegment.__table__).values(rows_to_insert)
                        do_update_stmt = stmt.on_conflict_do_update(
                            constraint='uq_transcription_segments_video_source_index',
                            set_=dict(
                                start=stmt.excluded.start,
                                duration=stmt.excluded.duration,
                                end=stmt.excluded.end,
                                text=stmt.excluded.text,
                                raw=stmt.excluded.raw,
                                updated_at=stmt.excluded.updated_at,
                            )
                        )
                        db.execute(do_update_stmt)

                    # Commit the transaction for this transcript
                    db.commit()
                except Exception:
                    # Rollback just this transcription's changes, continue with next transcript
                    try:
                        db.rollback()
                    except Exception:
                        pass
                    skipped += len(rows_to_insert)

            if t_idx % 50 == 0:
                print(f"Processed {t_idx}/{total} transcripts... inserted {inserted}, skipped {skipped}")

        print(f"Done. Inserted: {inserted}, Skipped (already existed): {skipped}")

    except Exception as exc:
        print(f"Error while populating segments: {exc}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def clear_segments_table():
    """Truncate the transcription_segments table (fast)"""
    with engine.connect() as conn:
        print("Clearing transcription_segments table...")
        with conn.begin():
            conn.execute(sa.text("TRUNCATE TABLE transcription_segments CASCADE;"))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Populate transcription_segments from transcripts')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of transcripts to process')
    parser.add_argument('--dry-run', action='store_true', help='Do not write to the database; just print actions')
    parser.add_argument('--clear', action='store_true', help='Clear transcription_segments table before importing')
    args = parser.parse_args()

    if args.clear:
        if args.dry_run:
            print("DRY RUN: would clear transcription_segments table")
        else:
            clear_segments_table()

    populate_segments(limit=args.limit, dry_run=args.dry_run, clear_flag=args.clear)
