"""
Butbul Halacha Ingest - Main entry point
"""

from dotenv import load_dotenv
import os


def main():
    """Main function to run the ingestion process."""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")

    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    if not youtube_api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable not set")

    print("Butbul Halacha Ingest - Starting...")
    print(f"Database URL: {database_url[:20]}...")
    print(f"YouTube API Key configured: {'Yes' if youtube_api_key else 'No'}")

    # TODO: Implement ingestion logic


if __name__ == "__main__":
    main()
