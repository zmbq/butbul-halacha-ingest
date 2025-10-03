"""
Extract metadata from video titles and descriptions.

This script parses the Hebrew date, day of week, and subject from video titles/descriptions
and populates the video_metadata table.

Title format: "הגאון הרב אהרון בוטבול - הלכה יומית - [Hebrew Date] - [Subject]"
Description format: "הלכה יומית - [Hebrew Date] - [Subject]"
"""

import re
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from ..database import get_db, Video, VideoMetadata
from ..hebrew_date_utils import get_day_of_week


def extract_hebrew_date_and_subject(text: str) -> tuple[str | None, str | None]:
    """
    Extract Hebrew date and subject from title or description.
    
    Expected patterns:
    - Title: "הגאון הרב אהרון בוטבול - הלכה יומית - [Hebrew Date] - [Subject]"
    - Description: "הלכה יומית - [Hebrew Date] - [Subject]"
    
    Args:
        text: Title or description text
        
    Returns:
        Tuple of (hebrew_date, subject)
    """
    if not text:
        return None, None
    
    # Remove the WhatsApp section from description if present
    text = text.split('\n\n')[0].strip()
    
    # Try to match the pattern: "הלכה יומית - [date] - [subject]"
    # This works for both title (after removing prefix) and description
    
    # Remove the "הגאון הרב אהרון בוטבול - " prefix if present
    if text.startswith("הגאון הרב אהרון בוטבול - "):
        text = text.replace("הגאון הרב אהרון בוטבול - ", "", 1)
    
    # Now we should have: "הלכה יומית - [date] - [subject]"
    if not text.startswith("הלכה יומית - "):
        return None, None
    
    # Remove "הלכה יומית - " prefix
    text = text.replace("הלכה יומית - ", "", 1)
    
    # Split by " - " to get date and subject
    parts = text.split(" - ", 1)
    
    if len(parts) < 2:
        # No subject, only date
        hebrew_date = parts[0].strip() if parts else None
        subject = None
    else:
        hebrew_date = parts[0].strip()
        subject = parts[1].strip()
    
    return hebrew_date, subject


def upsert_metadata_batch(db, metadata_batch: list) -> tuple[int, int]:
    """
    Insert or update a batch of video metadata records.
    
    Args:
        db: Database session
        metadata_batch: List of metadata dictionaries
        
    Returns:
        Tuple of (success_count, error_count)
    """
    if not metadata_batch:
        return 0, 0
    
    try:
        current_time = datetime.utcnow()
        insert_data = []
        
        for metadata in metadata_batch:
            insert_data.append({
                'video_id': metadata['video_id'],
                'hebrew_date': metadata['hebrew_date'],
                'day_of_week': metadata['day_of_week'],
                'subject': metadata['subject'],
                'created_at': current_time,
                'updated_at': current_time
            })
        
        # Use PostgreSQL's ON CONFLICT to handle upsert
        stmt = insert(VideoMetadata).values(insert_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['video_id'],
            set_={
                'hebrew_date': stmt.excluded.hebrew_date,
                'day_of_week': stmt.excluded.day_of_week,
                'subject': stmt.excluded.subject,
                'updated_at': stmt.excluded.updated_at
            }
        )
        
        db.execute(stmt)
        db.commit()
        return len(metadata_batch), 0
        
    except Exception as e:
        print(f"Error upserting metadata batch: {e}")
        db.rollback()
        return 0, len(metadata_batch)


def extract_all_metadata():
    """
    Extract metadata from all videos in the database.
    """
    print("=" * 80)
    print("Video Metadata Extraction")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    db = get_db()
    
    try:
        # Fetch all videos
        print("Fetching videos from database...")
        result = db.execute(select(Video))
        videos = result.scalars().all()
        print(f"Found {len(videos)} videos\n")
        
        if not videos:
            print("No videos found in database.")
            return
        
        # Process videos in batches
        print("Extracting metadata...")
        print("=" * 80)
        
        batch_size = 100
        success_count = 0
        error_count = 0
        extraction_errors = 0
        
        metadata_batch = []
        
        for i, video in enumerate(videos, 1):
            # Try to extract from title first, fall back to description
            hebrew_date, subject = extract_hebrew_date_and_subject(video.title)
            
            if not hebrew_date:
                # Try description if title extraction failed
                hebrew_date, subject = extract_hebrew_date_and_subject(video.description)
            
            # If hebrew_date is present but too long for DB, treat it as NULL
            if hebrew_date and len(hebrew_date) > 50:
                # Do not calculate day_of_week for overly long dates
                hebrew_date = None

            # Calculate day of week from the Hebrew date using proper conversion
            day_of_week = get_day_of_week(hebrew_date) if hebrew_date else None

            if not hebrew_date:
                extraction_errors += 1

            metadata_batch.append({
                'video_id': video.video_id,
                'hebrew_date': hebrew_date,
                'day_of_week': day_of_week,
                'subject': subject
            })
            
            # Process batch when full or at end
            if len(metadata_batch) >= batch_size or i == len(videos):
                batch_success, batch_error = upsert_metadata_batch(db, metadata_batch)
                success_count += batch_success
                error_count += batch_error
                
                status = "✓" if batch_error == 0 else "✗"
                print(f"{status} Processed {i}/{len(videos)} videos "
                      f"(Success: {success_count}, DB Errors: {error_count}, "
                      f"Extraction Errors: {extraction_errors})")
                
                metadata_batch = []
        
        # Print summary
        print(f"\n{'=' * 80}")
        print("Extraction Summary")
        print(f"{'=' * 80}")
        print(f"Total videos processed: {len(videos)}")
        print(f"Successfully stored metadata: {success_count}")
        print(f"Database errors: {error_count}")
        print(f"Extraction errors (no date found): {extraction_errors}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}\n")
        
        # Show some sample results
        if success_count > 0:
            print("Sample extracted metadata:")
            print("-" * 80)
            result = db.execute(select(VideoMetadata).limit(5))
            samples = result.scalars().all()
            for sample in samples:
                print(f"Video ID: {sample.video_id}")
                print(f"Hebrew Date: {sample.hebrew_date}")
                print(f"Day of Week: {sample.day_of_week}")
                print(f"Subject: {sample.subject}")
                print("-" * 80)
        
    finally:
        db.close()


if __name__ == "__main__":
    extract_all_metadata()
