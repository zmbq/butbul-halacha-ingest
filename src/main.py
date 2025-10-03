"""
Butbul Halacha Ingest - Main entry point
"""

from config import config


def main():
    """Main function to run the ingestion process."""
    print("Butbul Halacha Ingest - Starting...")
    print(f"Configuration loaded: {config}")
    
    # Configuration is now available via the config object
    # config.database_url
    # config.youtube_api_key
    # config.youtube_channel_id

    # TODO: Implement ingestion logic for הלכה יומית videos
    # 1. Connect to YouTube API using config.youtube_api_key
    # 2. Fetch videos from channel config.youtube_channel_id
    # 3. Filter for הלכה יומית videos
    # 4. Parse metadata (description, link, date from description)
    # 5. Store in database using config.database_url


if __name__ == "__main__":
    main()
