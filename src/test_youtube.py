"""
Simple test script to verify YouTube API connectivity and playlist discovery.
"""

from youtube_service import YouTubeService


def test_youtube_api():
    """Test YouTube API connectivity and playlist discovery."""
    print("Testing YouTube API connectivity...\n")
    
    try:
        service = YouTubeService()
        
        # Test 1: Get playlists with הלכה יומית filter
        print("=" * 80)
        print("Test 1: Finding playlists containing 'הלכה יומית'")
        print("=" * 80)
        playlists = service.get_playlists(name_filter="הלכה יומית")
        
        print(f"\nFound {len(playlists)} playlists:\n")
        for i, playlist in enumerate(playlists, 1):
            print(f"{i}. {playlist['title']}")
            print(f"   ID: {playlist['id']}")
            print(f"   Videos: {playlist['item_count']}")
            print(f"   Description: {playlist['description'][:100]}...")
            print()
        
        # Test 2: Get videos from first playlist (if any)
        if playlists:
            print("=" * 80)
            print(f"Test 2: Fetching videos from first playlist")
            print("=" * 80)
            first_playlist = playlists[0]
            videos = service.get_playlist_videos(first_playlist['id'])
            
            print(f"\nFound {len(videos)} videos. Showing first 5:\n")
            for i, video in enumerate(videos[:5], 1):
                print(f"{i}. {video['title']}")
                print(f"   Video ID: {video['video_id']}")
                print(f"   URL: {video['url']}")
                print(f"   Published: {video['published_at']}")
                print(f"   Description: {video['description'][:100]}...")
                print()
        
        print("=" * 80)
        print("✓ YouTube API test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during YouTube API test: {e}")
        raise


if __name__ == "__main__":
    test_youtube_api()
