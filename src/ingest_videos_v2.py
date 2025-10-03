"""
Video ingestion script - Step 1 of the pipeline (with JSON fallback).

This script:
1. Finds playlists containing "הלכה יומית" in their name
2. Fetches all videos from those playlists
3. Stores video metadata in database OR saves to JSON file if database unavailable
"""

import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from database import init_db, get_db, Video
from youtube_service import YouTubeService


def save_to_json(videos: list, filename: str = "videos_backup.json"):
    """
    Save videos to a JSON file as backup.

    Args:
        videos: List of video dictionaries
        filename: Output filename
    """
    output_path = Path(__file__).parent.parent / filename
    
    # Convert datetime objects to strings for JSON serialization
    videos_serializable = []
    for video in videos:
        video_copy = video.copy()
        if video_copy.get('published_at'):
            video_copy['published_at'] = video_copy['published_at'].isoformat()
        videos_serializable.append(video_copy)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(videos_serializable, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Videos saved to: {output_path}")
    return output_path


def upsert_video(db, video_data: dict) -> bool:
    """
    Insert or update a video record in the database.

    Args:
        db: Database session
        video_data: Dictionary with video information

    Returns:
        True if record was inserted/updated, False otherwise
    """
    try:
        # Prepare the data for insert
        insert_data = {
            'video_id': video_data['video_id'],
            'url': video_data['url'],
            'description': video_data['description'],
            'published_at': video_data['published_at'],
            'updated_at': datetime.utcnow()
        }

        # Use PostgreSQL's ON CONFLICT to handle upsert
        stmt = insert(Video).values(**insert_data)
        
        # Update all fields except video_id (primary key) and created_at on conflict
        stmt = stmt.on_conflict_do_update(
            index_elements=['video_id'],
            set_={
                'url': stmt.excluded.url,
                'description': stmt.excluded.description,
                'published_at': stmt.excluded.published_at,
                'updated_at': stmt.excluded.updated_at
            }
        )

        db.execute(stmt)
        db.commit()
        return True

    except Exception as e:
        print(f"Error upserting video {video_data['video_id']}: {e}")
        db.rollback()
        return False


def ingest_videos(playlist_filter: str = "הלכה יומית", save_json_backup: bool = True):
    """
    Main ingestion function.

    Args:
        playlist_filter: String to filter playlist names (default: "הלכה יומית")
        save_json_backup: Whether to save a JSON backup file
    """
    print("=" * 80)
    print("Butbul Halacha Video Ingestion - Step 1")
    print("=" * 80)
    print(f"\nSearching for playlists containing: '{playlist_filter}'")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Initialize YouTube service
    print("Connecting to YouTube API...")
    youtube_service = YouTubeService()

    # Get videos from filtered playlists
    print(f"\nFetching videos from playlists...")
    videos = youtube_service.get_videos_from_filtered_playlists(playlist_filter)

    if not videos:
        print("\nNo videos found matching the criteria.")
        return

    # Try to store in database, fall back to JSON if database unavailable
    database_available = False
    
    try:
        print("\nTrying to connect to database...")
        init_db()
        database_available = True
        print("✓ Database connection successful!")
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print("\n⚠ Will save to JSON file instead.")

    if database_available:
        # Store videos in database
        print(f"\n{'=' * 80}")
        print(f"Storing {len(videos)} videos in database...")
        print(f"{'=' * 80}\n")

        db = get_db()
        success_count = 0
        error_count = 0

        try:
            for i, video_data in enumerate(videos, 1):
                if upsert_video(db, video_data):
                    success_count += 1
                    status = "✓"
                else:
                    error_count += 1
                    status = "✗"

                # Print progress every 10 videos
                if i % 10 == 0 or i == len(videos):
                    print(f"{status} Processed {i}/{len(videos)} videos "
                          f"(Success: {success_count}, Errors: {error_count})")

        finally:
            db.close()

        # Print summary
        print(f"\n{'=' * 80}")
        print("Database Ingestion Summary")
        print(f"{'=' * 80}")
        print(f"Total videos processed: {len(videos)}")
        print(f"Successfully stored/updated: {success_count}")
        print(f"Errors: {error_count}")

    # Save JSON backup if requested or if database unavailable
    if save_json_backup or not database_available:
        print(f"\n{'=' * 80}")
        print("Saving JSON Backup")
        print(f"{'=' * 80}\n")
        json_path = save_to_json(videos)
        
        if not database_available:
            print(f"\n💡 To import this data when database is available, run:")
            print(f"   poetry run python src/import_from_json.py {json_path.name}")

    print(f"\n{'=' * 80}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    ingest_videos()
