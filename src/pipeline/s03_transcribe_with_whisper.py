"""
Whisper transcription script - Step 3 of the pipeline.

This script:
1. Fetches all videos from the database that don't have Whisper transcripts yet
2. Downloads audio using yt-dlp
3. Transcribes using OpenAI's Whisper API
4. Saves transcripts to BOTH database AND disk (data/transcripts/<video_id>.json)
5. Supports --test mode to process just one video (the oldest)
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
        'transcribed_at': datetime.utcnow().isoformat()
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
        print(f"  ✗ Error upserting transcript: {e}")
        db.rollback()
        return False


def transcribe_videos(max_videos: int = 10, delay_seconds: float = 1.0):
    """
    Main transcription function.
    
    Args:
        max_videos: Maximum number of videos to process (default: 10)
        delay_seconds: Delay in seconds between videos to avoid rate limiting
    """
    print("=" * 80)
    print("Butbul Halacha Whisper Transcription - Step 3")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Processing up to {max_videos} video{'s' if max_videos != 1 else ''}")
    print(f"Delay between videos: {delay_seconds} seconds\n")
    
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
    
    try:
        for idx, video in enumerate(videos, 1):
            video_id = video.video_id
            title = video.title[:60] + "..." if len(video.title) > 60 else video.title
            duration_min = (video.duration_seconds / 60) if video.duration_seconds else 0
            estimated_cost = duration_min * 0.006  # $0.006 per minute
            
            print(f"[{idx}/{total_videos}] Processing: {video_id}")
            print(f"  Title: {title}")
            print(f"  Published: {video.published_at}")
            print(f"  Duration: {duration_min:.1f} minutes")
            print(f"  Estimated cost: ${estimated_cost:.3f}")
            
            # Transcribe with Whisper
            transcript_data = transcript_service.transcribe_with_whisper(
                video_id=video_id,
                youtube_url=video.url
            )
            
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
                    total_cost += estimated_cost
                    segments = len(transcript_data['segments'])
                    chars = len(transcript_data['full_text'])
                    print(f"  ✓ Transcript saved (segments={segments}, chars={chars})")
                else:
                    error_count += 1
                    print(f"  ✗ Failed to save to database")
            else:
                error_count += 1
                print(f"  ✗ Transcription failed")
            
            # Add delay between videos
            if idx < total_videos:
                print(f"  ⏳ Waiting {delay_seconds} seconds...\n")
                time.sleep(delay_seconds)
            else:
                print()  # Blank line after last video
            
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
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    max_videos = 10  # Default to 10 videos
    delay_seconds = 1.0
    
    # Check for --count or -n flag
    if "--count" in sys.argv:
        count_idx = sys.argv.index("--count")
        if count_idx + 1 < len(sys.argv):
            try:
                max_videos = int(sys.argv[count_idx + 1])
            except ValueError:
                print(f"⚠️  Invalid count value, using default: {max_videos}\n")
    elif "-n" in sys.argv:
        count_idx = sys.argv.index("-n")
        if count_idx + 1 < len(sys.argv):
            try:
                max_videos = int(sys.argv[count_idx + 1])
            except ValueError:
                print(f"⚠️  Invalid count value, using default: {max_videos}\n")
    
    if "--delay" in sys.argv:
        delay_idx = sys.argv.index("--delay")
        if delay_idx + 1 < len(sys.argv):
            try:
                delay_seconds = float(sys.argv[delay_idx + 1])
            except ValueError:
                print(f"⚠️  Invalid delay value, using default: {delay_seconds} seconds\n")
    
    transcribe_videos(max_videos=max_videos, delay_seconds=delay_seconds)
