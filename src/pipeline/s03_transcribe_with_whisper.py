"""
Whisper transcription script - Step 3 of the pipeline.

This script:
1. Fetches all videos from the database that don't have Whisper transcripts yet
2. Downloads audio using yt-dlp (sequentially to avoid YouTube rate limiting)
3. Transcribes using OpenAI's Whisper API (in parallel batches)
4. Saves transcripts to BOTH database AND disk (data/transcripts/<video_id>.json)
5. Supports parallel processing with --parallel flag (default: 3 concurrent transcriptions)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from ..database import get_db, Video, Transcript
from ..transcript_service import TranscriptService
from ..config import config


def save_transcript_to_disk(video_id: str, transcript_data: dict, transcripts_dir: Path):
    """
    Save transcript to disk as JSON file.
    
    Args:
        video_id: YouTube video ID
        transcript_data: Transcript data dictionary
        transcripts_dir: Directory to save transcripts
    """
    # Create filename: <video_id>.json
    output_path = transcripts_dir / f"{video_id}.json"
    
    # Prepare data for JSON (ensure it's serializable)
    json_data = {
        'video_id': transcript_data['video_id'],
        'source': transcript_data['source'],
        'language': transcript_data['language'],
        'full_text': transcript_data['full_text'],
        'segments': transcript_data['segments'],
        'transcribed_at': datetime.now(timezone.utc).isoformat(),
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    return output_path


def upsert_transcript(db, transcript_data: dict) -> bool:
    """
    Insert or update a transcript record in the database.
    
    Args:
        db: Database session
        transcript_data: Transcript data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        current_time = datetime.now(timezone.utc)

        # Prepare data for insert
        insert_data = {
            'video_id': transcript_data['video_id'],
            'source': transcript_data['source'],
            'language': transcript_data['language'],
            'full_text': transcript_data['full_text'],
            'segments': transcript_data['segments'],
            'updated_at': current_time
        }
        
        # Use PostgreSQL's ON CONFLICT to handle upsert
        stmt = insert(Transcript).values(insert_data)
        
        # Update all fields on conflict
        stmt = stmt.on_conflict_do_update(
            index_elements=['video_id'],
            set_={
                'source': stmt.excluded.source,
                'language': stmt.excluded.language,
                'full_text': stmt.excluded.full_text,
                'segments': stmt.excluded.segments,
                'updated_at': stmt.excluded.updated_at
            }
        )
        
        db.execute(stmt)
        db.commit()
        return True
        
    except Exception as e:
        print(f"  ✗ Error upserting transcript: {e}")
        db.rollback()
        return False


def transcribe_single_video(video_data: dict, transcript_service: TranscriptService, transcripts_dir: Path, db_session):
    """
    Transcribe a single video (used for parallel processing).
    
    Args:
        video_data: Dictionary with video info (video_id, url, title, duration_seconds, published_at)
        transcript_service: TranscriptService instance
        transcripts_dir: Directory to save transcripts
        db_session: Database session
        
    Returns:
        Dictionary with result info
    """
    video_id = video_data['video_id']
    title = video_data['title'][:60] + "..." if len(video_data['title']) > 60 else video_data['title']
    duration_min = (video_data['duration_seconds'] / 60) if video_data['duration_seconds'] else 0
    estimated_cost = duration_min * 0.006
    
    print(f"\n[{video_id}] Starting transcription")
    print(f"  Title: {title}")
    print(f"  Duration: {duration_min:.1f} minutes")
    print(f"  Estimated cost: ${estimated_cost:.3f}")
    
    # Transcribe with Whisper
    transcript_data = transcript_service.transcribe_with_whisper(
        video_id=video_id,
        youtube_url=video_data['url']
    )
    
    if transcript_data:
        # Save to disk
        try:
            disk_path = save_transcript_to_disk(video_id, transcript_data, transcripts_dir)
            print(f"  ✓ [{video_id}] Saved to disk: {disk_path.name}")
        except Exception as e:
            print(f"  ✗ [{video_id}] Failed to save to disk: {e}")
            return {'success': False, 'video_id': video_id, 'cost': 0}
        
        # Save to database
        if upsert_transcript(db_session, transcript_data):
            segments = len(transcript_data['segments'])
            chars = len(transcript_data['full_text'])
            print(f"  ✓ [{video_id}] Transcript saved (segments={segments}, chars={chars})")
            return {'success': True, 'video_id': video_id, 'cost': estimated_cost}
        else:
            print(f"  ✗ [{video_id}] Failed to save to database")
            return {'success': False, 'video_id': video_id, 'cost': 0}
    else:
        print(f"  ✗ [{video_id}] Transcription failed")
        return {'success': False, 'video_id': video_id, 'cost': 0}


def transcribe_videos(max_videos: int = 10, delay_seconds: float = 1.0, parallel_workers: int = 3):
    """
    Main transcription function.
    
    Args:
        max_videos: Maximum number of videos to process (default: 10)
        delay_seconds: Delay in seconds between videos to avoid rate limiting
        parallel_workers: Number of parallel Whisper API calls (default: 3, max: 5)
    """
    # Limit parallel workers to 5
    parallel_workers = min(parallel_workers, 5)
    
    print("=" * 80)
    print("Butbul Halacha Whisper Transcription - Step 3")
    print("=" * 80)
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Processing up to {max_videos} video{'s' if max_videos != 1 else ''}")
    print(f"Parallel workers: {parallel_workers}")
    print(f"Delay between videos: {delay_seconds} seconds\n")
    
    # Initialize database
    try:
        print("Connecting to database...")
            # NOTE: do not create or modify tables here. Migrations (Alembic) manage schema.
        db = get_db()
        print("✓ Database connection successful!\n")
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # Create transcripts directory
    transcripts_dir = Path(config.data_dir) / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    print(f"Transcripts will be saved to: {transcripts_dir}\n")
    
    # Get videos to process (those without any transcript)
    print("Fetching videos from database...")
    
    query = (
        select(Video)
        .outerjoin(Transcript, Video.video_id == Transcript.video_id)
        .where(Transcript.video_id.is_(None))
        .order_by(Video.published_at.asc())  # Oldest first
        .limit(max_videos)
    )
    
    print(f"Selecting up to {max_videos} oldest videos without transcripts")
    
    videos = db.execute(query).scalars().all()
    total_videos = len(videos)
    
    if total_videos == 0:
        print("\nNo videos to process. All videos already have transcripts!")
        db.close()
        return
    
    print(f"\n{'=' * 80}")
    print(f"Processing {total_videos} video{'s' if total_videos > 1 else ''}")
    print(f"{'=' * 80}\n")
    
    # Initialize transcript service
    transcript_service = TranscriptService()
    
    # Track statistics
    success_count = 0
    error_count = 0
    total_cost = 0.0
    
    # Convert videos to dict format for parallel processing
    video_data_list = []
    for video in videos:
        video_data_list.append({
            'video_id': video.video_id,
            'url': video.url,
            'title': video.title,
            'duration_seconds': video.duration_seconds,
            'published_at': video.published_at
        })
    
    try:
        # Process videos in parallel batches
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            # Submit all tasks
            future_to_video = {}
            for idx, video_data in enumerate(video_data_list, 1):
                print(f"\n[{idx}/{total_videos}] Queuing: {video_data['video_id']}")
                future = executor.submit(
                    transcribe_single_video,
                    video_data,
                    transcript_service,
                    transcripts_dir,
                    db
                )
                future_to_video[future] = (idx, video_data)
                
                # Small delay between queuing to avoid overwhelming YouTube
                if idx < total_videos:
                    time.sleep(delay_seconds)
            
            # Collect results as they complete
            print(f"\n{'=' * 80}")
            print("Waiting for transcriptions to complete...")
            print(f"{'=' * 80}\n")
            
            for future in as_completed(future_to_video):
                idx, video_data = future_to_video[future]
                try:
                    result = future.result()
                    if result['success']:
                        success_count += 1
                        total_cost += result['cost']
                        print(f"✓ Completed {success_count}/{total_videos}: {result['video_id']}")
                    else:
                        error_count += 1
                        print(f"✗ Failed {error_count}/{total_videos}: {result['video_id']}")
                except Exception as e:
                    error_count += 1
                    print(f"✗ Exception for {video_data['video_id']}: {e}")
            
    finally:
        db.close()
    
    # Print summary
    print(f"{'=' * 80}")
    print("Whisper Transcription Summary")
    print(f"{'=' * 80}")
    print(f"Total videos processed: {total_videos}")
    print(f"Transcripts successfully created: {success_count}")
    print(f"Errors: {error_count}")
    if success_count > 0:
        print(f"\nEstimated total cost: ${total_cost:.2f}")
        print(f"Success rate: {(success_count/total_videos*100):.1f}%")
    print(f"Completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Run Whisper transcription pipeline')
    parser.add_argument('--count', '-n', type=int, default=10, help='Maximum number of videos to process')
    parser.add_argument('--parallel', '-p', type=int, default=3, help='Number of parallel Whisper API calls (max 5)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay in seconds between queuing videos')

    args = parser.parse_args()

    max_videos = args.count
    parallel_workers = min(args.parallel, 5)
    delay_seconds = args.delay

    transcribe_videos(max_videos=max_videos, delay_seconds=delay_seconds, parallel_workers=parallel_workers)
