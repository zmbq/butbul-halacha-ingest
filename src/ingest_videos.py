"""
Video ingestion script - Step 1 of the pipeline.

This script:
1. Finds playlists containing "הלכה יומית" in their name
2. Fetches all videos from those playlists
3. Saves video metadata to BOTH database AND JSON file simultaneously
"""

import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from src.database import init_db, get_db, Video
from src.youtube_service import YouTubeService


def save_to_json(videos: list, filename: str = "videos_backup.json"):
    """
    Save videos to a JSON file as backup.

    Args:
        videos: List of video dictionaries
        filename: Output filename (will be saved in data/ directory)
    """
    # Save to data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    output_path = data_dir / filename
    
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


def upsert_videos_batch(db, videos_batch: list) -> tuple[int, int]:
    """
    Insert or update a batch of video records in the database.

    Args:
        db: Database session
        videos_batch: List of video dictionaries

    Returns:
        Tuple of (success_count, error_count)
    """
    if not videos_batch:
        return 0, 0
    
    try:
        # Prepare batch data for insert
        current_time = datetime.utcnow()
        insert_data = []
        
        for video_data in videos_batch:
            insert_data.append({
                'video_id': video_data['video_id'],
                'url': video_data['url'],
                'description': video_data['description'],
                'published_at': video_data['published_at'],
                'updated_at': current_time
            })

        # Use PostgreSQL's ON CONFLICT to handle upsert for the entire batch
        stmt = insert(Video).values(insert_data)
        
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
        return len(videos_batch), 0

    except Exception as e:
        print(f"Error upserting batch: {e}")
        db.rollback()
        return 0, len(videos_batch)


def ingest_videos(playlist_filter: str = "הלכה יומית"):
    """
    Main ingestion function. Saves to BOTH database AND JSON simultaneously.

    Args:
        playlist_filter: String to filter playlist names (default: "הלכה יומית")
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

    # Always save JSON backup first (as a safety measure)
    print(f"\n{'=' * 80}")
    print("Saving JSON Backup")
    print(f"{'=' * 80}\n")
    json_path = save_to_json(videos)
    
    # Try to connect to database
    database_available = False
    
    try:
        print("\nConnecting to database...")
        init_db()
        database_available = True
        print("✓ Database connection successful!")
    except OperationalError as e:
        print(f"✗ Database connection failed: {e}")
        print("\n⚠ Data saved to JSON only. Database not updated.")

    # If database is available, also store there
    if database_available:
        print(f"\n{'=' * 80}")
        print(f"Storing {len(videos)} videos in database (batch size: 100)...")
        print(f"{'=' * 80}\n")

        db = get_db()
        success_count = 0
        error_count = 0
        batch_size = 100

        try:
            # Process videos in batches
            for i in range(0, len(videos), batch_size):
                batch = videos[i:i + batch_size]
                batch_success, batch_error = upsert_videos_batch(db, batch)
                success_count += batch_success
                error_count += batch_error
                
                # Print progress
                processed = min(i + batch_size, len(videos))
                status = "✓" if batch_error == 0 else "✗"
                print(f"{status} Processed {processed}/{len(videos)} videos "
                      f"(Success: {success_count}, Errors: {error_count})")

        finally:
            db.close()

        # Print database summary
        print(f"\n{'=' * 80}")
        print("Database Ingestion Summary")
        print(f"{'=' * 80}")
        print(f"Total videos processed: {len(videos)}")
        print(f"Successfully stored/updated: {success_count}")
        print(f"Errors: {error_count}")

    # Final summary
    print(f"\n{'=' * 80}")
    print("Final Summary")
    print(f"{'=' * 80}")
    print(f"Total videos collected: {len(videos)}")
    print(f"JSON backup: {json_path}")
    if database_available:
        print(f"Database: ✓ Updated successfully")
    else:
        print(f"Database: ✗ Not updated (connection failed)")
        print(f"\n💡 To import JSON to database later, run:")
        print(f"   poetry run python src/import_from_json.py data/{json_path.name}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    ingest_videos()
