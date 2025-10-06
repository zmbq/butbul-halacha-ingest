"""
Create embeddings for subjects and chunks.

This pipeline step embeds either 'subjects', 'chunks', or 'everything'. It
supports --limit, --dry-run and --batch-size flags and is designed to be
invoked from `src.cli` as `s06`.
"""
from __future__ import annotations

import argparse

from typing import List, Optional
from time import perf_counter

from ..database import get_db, VideoMetadata, TranscriptionChunk, EmbeddingCache, Embedding
from typing import List as _List
from ..embedding_service import EmbeddingService, EmbeddingWithCache
from sqlalchemy import select


def populate_embeddings(kind: str, limit: Optional[int] = None, batch_size: int = 64, dry_run: bool = False):
    """Embed items of the requested kind.

    kind: 'subjects' | 'chunks' | 'everything'
    """
    if kind not in ('subjects', 'chunks', 'everything'):
        raise ValueError("kind must be one of 'subjects', 'chunks', 'everything'")

    svc = EmbeddingService()
    db = get_db()
    # Counters for summary
    total_processed = 0
    total_created = 0
    total_skipped = 0
    total_errors = 0
    start_time = perf_counter()
    try:
        # SUBJECTS
        if kind in ('subjects', 'everything'):
            stmt = select(VideoMetadata).order_by(VideoMetadata.video_id)
            if limit:
                stmt = stmt.limit(limit)
            rows = db.execute(stmt).scalars().all()
            items = [r for r in rows if getattr(r, 'subject', None)]
            texts = [str(getattr(r, 'subject')) for r in items]

            # batch and call service
            total_items = len(texts)
            num_batches = (total_items + batch_size - 1) // batch_size
            print(f"Will process {total_items} subjects in {num_batches} batches (batch_size={batch_size})")
            for batch_index, i in enumerate(range(0, len(texts), batch_size), start=1):
                batch_texts = texts[i:i+batch_size]
                batch_items = items[i:i+batch_size]
                batch_start = perf_counter()
                print(f"Starting subjects batch {batch_index}/{num_batches} with {len(batch_items)} items...")
                try:
                    pairs = svc.embed_bulk_with_cache(db, batch_texts)
                except Exception as e:
                    total_errors += len(batch_items)
                    print(f"ERROR: embed_bulk failed for subjects batch {batch_index}: {e}")
                    continue

                if dry_run:
                    total_processed += len(batch_items)
                    batch_elapsed = perf_counter() - batch_start
                    avg = (perf_counter() - start_time) / max(1, total_processed)
                    remaining = max(0, total_items - total_processed)
                    eta = remaining * avg
                    print(f"DRY: processed {len(batch_items)} subjects (batch {batch_index}) — {total_processed}/{total_items} ({total_processed/total_items:.0%}) elapsed={batch_elapsed:.2f}s eta={eta:.1f}s")
                    continue

                # Persist Embedding rows; skip if embedding for same video/kind/model already exists
                created_this_batch = 0
                skipped_this_batch = 0
                for item, pair in zip(batch_items, pairs):
                    cache_row = pair.cache_row
                    try:
                        if cache_row is None:
                            skipped_this_batch += 1
                            continue
                        exists = db.query(Embedding).filter_by(video_id=item.video_id, kind='subject', model=svc.model).one_or_none()
                        if exists:
                            skipped_this_batch += 1
                            continue
                        emb = Embedding(video_id=item.video_id, transcription_chunk_id=None, kind='subject', source_cache_id=cache_row.id)
                        db.add(emb)
                        created_this_batch += 1
                    except Exception as e:
                        total_errors += 1
                        print(f"ERROR: failed to persist subject embedding for video {getattr(item, 'video_id', None)}: {e}")
                db.commit()
                batch_elapsed = perf_counter() - batch_start
                total_processed += len(batch_items)
                total_created += created_this_batch
                total_skipped += skipped_this_batch
                avg = (perf_counter() - start_time) / max(1, total_processed)
                remaining = max(0, total_items - total_processed)
                eta = remaining * avg
                print(f"Batch {batch_index}: subjects processed={len(batch_items)}, created={created_this_batch}, skipped={skipped_this_batch} — {total_processed}/{total_items} ({total_processed/total_items:.0%}) elapsed={batch_elapsed:.2f}s eta={eta:.1f}s")

        # CHUNKS
        if kind in ('chunks', 'everything'):
            stmt = select(TranscriptionChunk).order_by(TranscriptionChunk.id)
            if limit:
                stmt = stmt.limit(limit)
            rows = db.execute(stmt).scalars().all()
            items = rows
            texts = [str(getattr(r, 'text', '')) for r in items]

            total_items = len(texts)
            num_batches = (total_items + batch_size - 1) // batch_size
            print(f"Will process {total_items} chunks in {num_batches} batches (batch_size={batch_size})")
            for batch_index, i in enumerate(range(0, len(texts), batch_size), start=1):
                batch_texts = texts[i:i+batch_size]
                batch_items = items[i:i+batch_size]
                batch_start = perf_counter()
                print(f"Starting chunks batch {batch_index}/{num_batches} with {len(batch_items)} items...")
                try:
                    pairs = svc.embed_bulk_with_cache(db, batch_texts)
                except Exception as e:
                    total_errors += len(batch_items)
                    print(f"ERROR: embed_bulk failed for chunks batch {batch_index}: {e}")
                    continue

                if dry_run:
                    total_processed += len(batch_items)
                    batch_elapsed = perf_counter() - batch_start
                    avg = (perf_counter() - start_time) / max(1, total_processed)
                    remaining = max(0, total_items - total_processed)
                    eta = remaining * avg
                    print(f"DRY: processed {len(batch_items)} chunks (batch {batch_index}) — {total_processed}/{total_items} ({total_processed/total_items:.0%}) elapsed={batch_elapsed:.2f}s eta={eta:.1f}s")
                    continue

                created_this_batch = 0
                skipped_this_batch = 0
                for item, pair in zip(batch_items, pairs):
                    cache_row = pair.cache_row
                    try:
                        if cache_row is None:
                            skipped_this_batch += 1
                            continue
                        # skip if embedding exists for this chunk+model
                        exists = db.query(Embedding).filter_by(transcription_chunk_id=item.id, model=svc.model).one_or_none()
                        if exists:
                            skipped_this_batch += 1
                            continue
                        emb = Embedding(video_id=item.video_id, transcription_chunk_id=item.id, kind='chunk', source_cache_id=cache_row.id)
                        db.add(emb)
                        created_this_batch += 1
                    except Exception as e:
                        total_errors += 1
                        print(f"ERROR: failed to persist chunk embedding for chunk id {getattr(item, 'id', None)}: {e}")
                db.commit()
                batch_elapsed = perf_counter() - batch_start
                total_processed += len(batch_items)
                total_created += created_this_batch
                total_skipped += skipped_this_batch
                avg = (perf_counter() - start_time) / max(1, total_processed)
                remaining = max(0, total_items - total_processed)
                eta = remaining * avg
                print(f"Batch {batch_index}: chunks processed={len(batch_items)}, created={created_this_batch}, skipped={skipped_this_batch} — {total_processed}/{total_items} ({total_processed/total_items:.0%}) elapsed={batch_elapsed:.2f}s eta={eta:.1f}s")

    finally:
        db.close()
    # Print final summary
    print("\nEmbedding run summary:")
    print(f"  kind: {kind}")
    print(f"  total_processed: {total_processed}")
    print(f"  total_created:   {total_created}")
    print(f"  total_skipped:   {total_skipped}")
    print(f"  total_errors:    {total_errors}")


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description='Create embeddings for subjects and chunks')
    parser.add_argument('--kind', type=str, choices=['subjects', 'chunks', 'everything'], required=True, help='Which items to embed')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of items to process')
    parser.add_argument('--batch-size', type=int, default=64, help='Batch size for OpenAI calls')
    parser.add_argument('--dry-run', action='store_true', help='Do not write embeddings to DB')

    args = parser.parse_args(argv)
    populate_embeddings(kind=args.kind, limit=args.limit, batch_size=args.batch_size, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
