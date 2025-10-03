"""
Butbul Halacha Ingest - Main entry point
"""

from config import config
from ingest_videos_v2 import ingest_videos


def main():
    """Main function to run the ingestion process."""
    print("Butbul Halacha Ingest - Starting...")
    print(f"Configuration loaded: {config}\n")
    
    # Run Step 1: Ingest videos from הלכה יומית playlists
    # This will save to database if available, otherwise to JSON
    ingest_videos(playlist_filter="הלכה יומית")


if __name__ == "__main__":
    main()
