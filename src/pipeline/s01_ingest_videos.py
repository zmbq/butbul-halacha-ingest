"""
Video ingestion script - Step 1 of the pipeline.

This script:
1. Finds playlists containing "הלכה יומית" in their name
2. Fetches all videos from those playlists
3. Saves video metadata to BOTH database AND JSON file simultaneously
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from ..database import init_db, get_db, Video
from ..youtube_service import YouTubeService
from ..config import config


def save_to_json(videos: list, filename: str = "videos_backup.json"):
    """
    Save videos to a JSON file as backup.

    Args:
        videos: List of video dictionaries
        filename: Output filename (will be saved in data/ directory)
    """
    # Save to configured data directory
    data_dir = Path(config.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
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
                    'title': video_data.get('title', ''),
                    'description': video_data['description'],
                    'published_at': video_data['published_at'],
                    'duration_seconds': video_data.get('duration_seconds'),
                    'updated_at': current_time
                })        # Use PostgreSQL's ON CONFLICT to handle upsert for the entire batch
        stmt = insert(Video).values(insert_data)
        
        # Update all fields except video_id (primary key) and created_at on conflict
        stmt = stmt.on_conflict_do_update(
            index_elements=['video_id'],
            set_={
                'url': stmt.excluded.url,
                'title': stmt.excluded.title,
                'description': stmt.excluded.description,
                'published_at': stmt.excluded.published_at,
                'duration_seconds': stmt.excluded.duration_seconds,
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
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

    # Initialize YouTube service
    print("Connecting to YouTube API...")
    youtube_service = YouTubeService()

    # Get videos from filtered playlists
    print(f"\nFetching videos from playlists...")
    videos = youtube_service.get_videos_from_filtered_playlists(playlist_filter)

    if not videos:
        print("\nNo videos found matching the criteria.")
        return

    # Fetch duration details for all videos
    print(f"\nFetching duration details for {len(videos)} videos...")
    video_ids = [v['video_id'] for v in videos]
    
    # Process in batches of 50 (YouTube API limit)
    batch_size = 50
    for i in range(0, len(video_ids), batch_size):
        batch_ids = video_ids[i:i + batch_size]
        details = youtube_service.get_video_details(batch_ids)
        
        # Update videos with duration information
        for video in videos:
            if video['video_id'] in details:
                video['duration_seconds'] = details[video['video_id']]['duration_seconds']
        
        processed = min(i + batch_size, len(video_ids))
        print(f"  Fetched details for {processed}/{len(video_ids)} videos")
    
    print(f"✓ Duration details fetched successfully")

    # Filter out videos longer than 10 minutes (600 seconds)
    max_duration_seconds = 10 * 60
    long_videos = [v for v in videos if v.get('duration_seconds') and v['duration_seconds'] > max_duration_seconds]
    if long_videos:
        print(f"\nDetected {len(long_videos)} video(s) longer than 10 minutes. These will be skipped and not stored.")
        for v in long_videos:
            print(f"  - Skipping {v['video_id']} ({v.get('duration_seconds')}s): {v.get('title')}")

    # Keep only videos not exceeding the maximum duration (or without duration info)
    videos = [v for v in videos if not (v.get('duration_seconds') and v['duration_seconds'] > max_duration_seconds)]

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
    print(f"Completed at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Ingest videos from YouTube playlists')
    parser.add_argument('--filter', type=str, default='הלכה יומית', help='Playlist name filter string')
    args = parser.parse_args()

    ingest_videos(playlist_filter=args.filter)
