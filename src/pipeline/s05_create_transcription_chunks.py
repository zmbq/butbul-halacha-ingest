"""
Create transcription chunks for embeddings.

Chunks are built from contiguous transcription segments. Each chunk should be
approximately 20-30 seconds long (target) and should overlap with the previous
chunk by 1 segment. For example, if chunk covers segments 1-5, the next chunk
will cover 5-9 (segment 5 overlapped).

This script populates the `transcription_chunks` table with rows pointing to the
first and last segment ids (inclusive). It supports --limit (number of videos),
--dry-run and --clear flags.
"""

from __future__ import annotations

import argparse
from typing import List, Optional
from math import isclose
from datetime import datetime, timezone

from ..database import get_db, TranscriptionSegment, TranscriptionChunk, Transcript
from sqlalchemy import select, func
import sqlalchemy as sa


TARGET_MIN_SECONDS = 20.0
TARGET_MAX_SECONDS = 30.0
OVERLAP_SEGMENTS = 1  # number of segments to overlap between chunks


def build_chunks_for_segments(segments: List[TranscriptionSegment]) -> List[dict]:
    """Given an ordered list of TranscriptionSegment ORM objects (sorted by segment_index),
    return a list of chunk dicts with keys: first_segment_id, last_segment_id, start, end.

    Algorithm:
    - Start at the first segment index i.
    - Keep adding segments until chunk duration (end - start) reaches at least TARGET_MIN_SECONDS.
    - If chunk duration exceeds TARGET_MAX_SECONDS by adding a segment, try to stop before that segment.
    - Ensure each chunk has at least one segment and at most consumes all remaining segments.
    - Next chunk starts at index (last_index - OVERLAP_SEGMENTS + 1) to provide overlap.
    """
    if not segments:
        return []

    # Helper to compute start and end seconds for a range of segments
    def range_start_end(seg_list, start_idx, end_idx):
        s = seg_list[start_idx].start
        e = seg_list[end_idx].end
        return s, e

    chunks = []
    n = len(segments)
    i = 0

    while i < n:
        j = i
        start_sec = segments[i].start
        end_sec = segments[j].end

        # Expand until we reach minimum target seconds or run out
        while j + 1 < n:
            # tentative next end if we include next segment
            tentative_end = segments[j + 1].end
            tentative_duration = tentative_end - start_sec

            # If we haven't reached min seconds, extend
            if tentative_duration < TARGET_MIN_SECONDS:
                j += 1
                end_sec = tentative_end
                continue

            # If we've reached between min and max, prefer to stop now
            if TARGET_MIN_SECONDS <= tentative_duration <= TARGET_MAX_SECONDS:
                j += 1
                end_sec = tentative_end
                break

            # If tentative would exceed max, then decide whether to include or stop
            if tentative_duration > TARGET_MAX_SECONDS:
                # If current duration already >= TARGET_MIN_SECONDS, stop here
                current_duration = end_sec - start_sec
                if current_duration >= TARGET_MIN_SECONDS:
                    break
                else:
                    # We must include the next segment to reach minimum
                    j += 1
                    end_sec = tentative_end
                    break

        # Create chunk covering i..j inclusive
        first_seg_id = segments[i].id
        last_seg_id = segments[j].id
        start_sec = segments[i].start
        end_sec = segments[j].end

        chunks.append({
            'first_segment_id': first_seg_id,
            'last_segment_id': last_seg_id,
            'start': start_sec,
            'end': end_sec,
            # aggregated text will be filled later when we have access to segment texts
            'text': None,
        })

        # Advance i to start of next chunk, overlapping by OVERLAP_SEGMENTS
        # next_i should be j - OVERLAP_SEGMENTS + 1
        next_i = j - OVERLAP_SEGMENTS + 1
        if next_i <= i:
            # ensure progress at least by 1 to avoid infinite loop
            next_i = j + 1
        i = next_i

    return chunks


def populate_chunks(limit: Optional[int] = None, dry_run: bool = False, clear_flag: bool = False):
    db = get_db()
    try:

        # Optionally clear existing chunks
        if clear_flag and not dry_run:
            print("Clearing transcription_chunks table...")
            db.execute(sa.text("TRUNCATE TABLE transcription_chunks CASCADE;"))
            db.commit()

        # Find videos that have segments
        stmt = select(Transcript.video_id, Transcript.source, func.jsonb_array_length(Transcript.segments).label('seg_count'))
        stmt = stmt.where(Transcript.segments != None)
        stmt = stmt.order_by(Transcript.video_id)
        if limit:
            stmt = stmt.limit(limit)

        result = db.execute(stmt)
        transcripts = result.fetchall()

        print(f"Found {len(transcripts)} transcripts with segments to process")

        total_chunks = 0
        total_saved = 0

        total_transcripts = len(transcripts)
        for t_idx, row in enumerate(transcripts, start=1):
            video_id = row.video_id
            source = row.source

            # Load segments for this video ordered by segment_index
            seg_stmt = select(TranscriptionSegment).where(TranscriptionSegment.video_id == video_id, TranscriptionSegment.source == source).order_by(TranscriptionSegment.segment_index)
            segs_res = db.execute(seg_stmt)
            segments = segs_res.scalars().all()

            if not segments:
                continue

            chunks = build_chunks_for_segments(segments)
            total_chunks += len(chunks)

            if dry_run:
                for idx, c in enumerate(chunks):
                    print(f"DRY: chunk {idx} video={video_id} first_seg={c['first_segment_id']} last_seg={c['last_segment_id']} start={c['start']} end={c['end']}")
                print(f"DRY: video {t_idx}/{total_transcripts} ({video_id}) -> chunks: {len(chunks)}")
                continue

            # Fill aggregated text for each chunk by concatenating segment.text in order
            # Build a mapping from segment id -> text for quick lookup
            seg_texts = {s.id: (s.text or '') for s in segments}
            for c in chunks:
                # Collect texts for segment ids in range
                # find index positions of first/last ids in segments list
                first_idx = next((idx for idx, s in enumerate(segments) if s.id == c['first_segment_id']), None)
                last_idx = next((idx for idx, s in enumerate(segments) if s.id == c['last_segment_id']), None)
                if first_idx is None or last_idx is None:
                    c['text'] = ''
                else:
                    texts = [segments[k].text for k in range(first_idx, last_idx + 1)]
                    # join with single space
                    c['text'] = ' '.join(t.strip() for t in texts if t is not None)

            # Use SQLAlchemy Core bulk upsert (ON CONFLICT) per video in a single transaction
            from sqlalchemy.dialects.postgresql import insert
            chunk_table = TranscriptionChunk.__table__
            insert_rows = []
            for c in chunks:
                insert_rows.append({
                    'video_id': video_id,
                    'source': source,
                    'first_segment_id': c['first_segment_id'],
                    'last_segment_id': c['last_segment_id'],
                    'start': c['start'],
                    'end': c['end'],
                    'text': c['text'],
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc),
                })

            saved_for_video = 0
            if insert_rows:
                stmt = insert(chunk_table).values(insert_rows)
                # conflict target is the unique constraint on (video_id, first_segment_id, last_segment_id)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['video_id', 'first_segment_id', 'last_segment_id'],
                    set_={
                        'start': stmt.excluded.start,
                        'end': stmt.excluded.end,
                        'text': stmt.excluded.text,
                        'updated_at': stmt.excluded.updated_at,
                    }
                )
                db.execute(stmt)
                db.commit()
                saved_for_video = len(insert_rows)
                total_saved += saved_for_video

            # Per-video progress output
            print(f"Processed {t_idx}/{total_transcripts} video={video_id}: chunks_generated={len(chunks)}, chunks_saved={saved_for_video}")

            # Periodic status every 10 videos
            if t_idx % 10 == 0:
                print(f"Status: processed {t_idx}/{total_transcripts} videos, total_chunks={total_chunks}, total_saved={total_saved}")

        print(f"Done. Total chunks generated: {total_chunks}, saved: {total_saved}")
    finally:
        db.close()


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Create transcription chunks for embeddings")
    parser.add_argument("--limit", type=int, help="Limit number of transcripts to process")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB; just print actions")
    parser.add_argument("--clear", action="store_true", help="Clear transcription_chunks before inserting")

    args = parser.parse_args(argv)
    populate_chunks(limit=args.limit, dry_run=args.dry_run, clear_flag=args.clear)


if __name__ == '__main__':
    main()
