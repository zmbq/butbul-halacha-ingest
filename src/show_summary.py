"""
Display summary of collected videos from JSON file.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import Counter


def show_summary(json_file: str = "videos_backup.json"):
    """
    Show summary statistics of collected videos.

    Args:
        json_file: Path to JSON file containing videos
    """
    json_path = Path(__file__).parent.parent / json_file
    
    if not json_path.exists():
        print(f"✗ Error: File not found: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    print("=" * 80)
    print("הלכה יומית - Video Collection Summary")
    print("=" * 80)
    print(f"\nTotal Videos: {len(videos)}\n")

    # Extract years from titles
    years = []
    for video in videos:
        title = video.get('title', '')
        # Look for Hebrew year patterns like תשפ"ו
        if 'תשפ"ו' in title:
            years.append('תשפ"ו (5786)')
        elif 'תשפ"ה' in title:
            years.append('תשפ"ה (5785)')
        elif 'תשפ"ד' in title:
            years.append('תשפ"ד (5784)')
        elif 'תשפ"ג' in title:
            years.append('תשפ"ג (5783)')
        elif 'תשפ"ב' in title:
            years.append('תשפ"ב (5782)')

    # Count by year
    year_counts = Counter(years)
    
    print("Videos by Year:")
    print("-" * 80)
    for year, count in sorted(year_counts.items(), reverse=True):
        print(f"  {year}: {count} videos")

    # Date range
    dates = []
    for video in videos:
        if video.get('published_at'):
            try:
                date = datetime.fromisoformat(video['published_at'])
                dates.append(date)
            except:
                pass

    if dates:
        print(f"\n\nDate Range:")
        print("-" * 80)
        print(f"  Earliest: {min(dates).strftime('%Y-%m-%d')}")
        print(f"  Latest: {max(dates).strftime('%Y-%m-%d')}")

    # Sample videos
    print(f"\n\nSample Videos (first 5):")
    print("-" * 80)
    for i, video in enumerate(videos[:5], 1):
        title = video.get('title', 'No title')
        video_id = video.get('video_id', 'unknown')
        pub_date = video.get('published_at', 'No date')
        if pub_date != 'No date':
            try:
                pub_date = datetime.fromisoformat(pub_date).strftime('%Y-%m-%d')
            except:
                pass
        
        print(f"\n{i}. {title}")
        print(f"   ID: {video_id}")
        print(f"   Date: {pub_date}")
        print(f"   URL: {video.get('url', 'No URL')}")
        desc = video.get('description', '')
        if desc:
            print(f"   Description: {desc[:100]}...")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    show_summary()
