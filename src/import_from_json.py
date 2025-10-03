"""
Import videos from JSON backup file to database.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from src.database import init_db, get_db, Video
from sqlalchemy.dialects.postgresql import insert


def import_from_json(json_file: str):
    """
    Import videos from JSON file to database.

    Args:
        json_file: Path to JSON file containing videos
    """
    print("=" * 80)
    print("Importing Videos from JSON to Database")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Read JSON file
    json_path = Path(json_file)
    if not json_path.exists():
        print(f"✗ Error: File not found: {json_path}")
        return

    print(f"Reading from: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    print(f"Found {len(videos)} videos in JSON file\n")

    # Initialize database
    print("Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully!\n")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return

    # Import videos
    db = get_db()
    success_count = 0
    error_count = 0

    print("Importing videos...")
    print("=" * 80)

    try:
        for i, video_data in enumerate(videos, 1):
            try:
                # Convert date string back to datetime if present
                if video_data.get('published_at'):
                    video_data['published_at'] = datetime.fromisoformat(
                        video_data['published_at']
                    )

                # Prepare insert data
                insert_data = {
                    'video_id': video_data['video_id'],
                    'url': video_data['url'],
                    'description': video_data['description'],
                    'published_at': video_data['published_at'],
                    'updated_at': datetime.utcnow()
                }

                # Use PostgreSQL's ON CONFLICT to handle upsert
                stmt = insert(Video).values(**insert_data)
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
                success_count += 1

                # Print progress
                if i % 50 == 0 or i == len(videos):
                    print(f"✓ Processed {i}/{len(videos)} videos "
                          f"(Success: {success_count}, Errors: {error_count})")

            except Exception as e:
                error_count += 1
                print(f"✗ Error importing video {video_data.get('video_id', 'unknown')}: {e}")
                db.rollback()

    finally:
        db.close()

    # Print summary
    print("\n" + "=" * 80)
    print("Import Summary")
    print("=" * 80)
    print(f"Total videos in file: {len(videos)}")
    print(f"Successfully imported: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_from_json.py <json_file>")
        print("Example: python import_from_json.py videos_backup.json")
        sys.exit(1)

    import_from_json(sys.argv[1])
