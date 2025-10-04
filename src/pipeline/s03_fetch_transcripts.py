"""
Transcript fetching script - Step 3 of the pipeline.

This script:
1. Fetches all videos from the database that don't have transcripts yet
2. Attempts to fetch YouTube transcripts for each video
3. Saves transcripts to BOTH database AND disk (data/transcripts/<video_id>.json)
4. Tracks which videos have transcripts and which don't
5. Includes configurable delay between requests to avoid rate limiting
"""

import json
import time
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from ..database import init_db, get_db, Video, Transcript
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
        'fetched_at': datetime.utcnow().isoformat()
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
        current_time = datetime.utcnow()
        
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
        print(f"Error upserting transcript for {transcript_data['video_id']}: {e}")
        db.rollback()
        return False


def fetch_transcripts(skip_existing: bool = True, max_videos: int | None = None, delay_seconds: float = 1.0):
    """
    Main transcript fetching function.
    
    Args:
        skip_existing: If True, skip videos that already have transcripts
        max_videos: Maximum number of videos to process (None = all)
        delay_seconds: Delay in seconds between requests to avoid rate limiting (default: 1.0)
    """
    print("=" * 80)
    print("Butbul Halacha Transcript Fetching - Step 3")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Delay between requests: {delay_seconds} seconds\n")
    
    # Initialize database
    try:
        print("Connecting to database...")
        init_db()
        db = get_db()
        print("✓ Database connection successful!\n")
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # Create transcripts directory
    transcripts_dir = Path(config.data_dir) / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    print(f"Transcripts will be saved to: {transcripts_dir}\n")
    
    # Get videos to process
    print("Fetching videos from database...")
    
    if skip_existing:
        # Get videos without transcripts
        query = (
            select(Video)
            .outerjoin(Transcript, Video.video_id == Transcript.video_id)
            .where(Transcript.video_id.is_(None))
        )
        print("Mode: Processing only videos without transcripts")
    else:
        # Get all videos
        query = select(Video)
        print("Mode: Processing all videos (will overwrite existing transcripts)")
    
    if max_videos:
        query = query.limit(max_videos)
        print(f"Limit: Processing maximum {max_videos} videos")
    
    videos = db.execute(query).scalars().all()
    total_videos = len(videos)
    
    if total_videos == 0:
        print("\nNo videos to process.")
        db.close()
        return
    
    print(f"\n{'=' * 80}")
    print(f"Processing {total_videos} videos")
    print(f"{'=' * 80}\n")
    
    # Initialize transcript service
    transcript_service = TranscriptService()
    
    # Track statistics
    success_count = 0
    no_transcript_count = 0
    error_count = 0
    
    try:
        for idx, video in enumerate(videos, 1):
            video_id = video.video_id
            title = video.title[:60] + "..." if len(video.title) > 60 else video.title
            
            print(f"[{idx}/{total_videos}] Processing: {video_id}")
            print(f"  Title: {title}")
            
            # Fetch transcript from YouTube
            transcript_data = transcript_service.fetch_youtube_transcript(video_id)
            
            if transcript_data:
                # Save to disk
                try:
                    disk_path = save_transcript_to_disk(video_id, transcript_data, transcripts_dir)
                    print(f"  ✓ Saved to disk: {disk_path.name}")
                except Exception as e:
                    print(f"  ✗ Failed to save to disk: {e}")
                    error_count += 1
                    continue
                
                # Save to database
                if upsert_transcript(db, transcript_data):
                    success_count += 1
                    lang = transcript_data['language']
                    segments = len(transcript_data['segments'])
                    chars = len(transcript_data['full_text'])
                    print(f"  ✓ Transcript saved (lang={lang}, segments={segments}, chars={chars})")
                else:
                    error_count += 1
                    print(f"  ✗ Failed to save to database")
            else:
                no_transcript_count += 1
                print(f"  ⊘ No transcript available")
            
            # Add delay between requests to avoid rate limiting
            if idx < total_videos:  # Don't delay after the last video
                time.sleep(delay_seconds)
            
            print()  # Blank line between videos
            
    finally:
        db.close()
    
    # Print summary
    print(f"{'=' * 80}")
    print("Transcript Fetching Summary")
    print(f"{'=' * 80}")
    print(f"Total videos processed: {total_videos}")
    print(f"Transcripts successfully fetched: {success_count}")
    print(f"No transcript available: {no_transcript_count}")
    print(f"Errors: {error_count}")
    print(f"\nSuccess rate: {(success_count/total_videos*100):.1f}%")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    skip_existing = True
    max_videos = None
    delay_seconds = 1.0  # Default 1 second delay
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            skip_existing = False
        elif sys.argv[1] == "--test":
            max_videos = 10
            print("\n🧪 TEST MODE: Processing only 10 videos\n")
        
        # Check for --delay argument
        if "--delay" in sys.argv:
            delay_idx = sys.argv.index("--delay")
            if delay_idx + 1 < len(sys.argv):
                try:
                    delay_seconds = float(sys.argv[delay_idx + 1])
                    print(f"⏱️  Using custom delay: {delay_seconds} seconds\n")
                except ValueError:
                    print(f"⚠️  Invalid delay value, using default: {delay_seconds} seconds\n")
    
    fetch_transcripts(skip_existing=skip_existing, max_videos=max_videos, delay_seconds=delay_seconds)
