"""
Test YouTube API service functionality.
"""

import pytest
from src.youtube_service import YouTubeService


def test_youtube_service_initialization():
    """Test that YouTubeService can be initialized."""
    service = YouTubeService()
    assert service is not None
    assert service.youtube is not None
    assert service.api_key is not None
    assert service.channel_id is not None


def test_get_playlists_with_filter():
    """Test getting playlists with הלכה יומית filter."""
    service = YouTubeService()
    playlists = service.get_playlists(name_filter="הלכה יומית")
    
    # Should find at least one playlist
    assert len(playlists) > 0
    
    # Each playlist should have required fields
    for playlist in playlists:
        assert 'id' in playlist
        assert 'title' in playlist
        assert 'item_count' in playlist
        assert 'הלכה יומית' in playlist['title']


def test_get_playlist_videos():
    """Test getting videos from a specific playlist."""
    service = YouTubeService()
    
    # First get a playlist
    playlists = service.get_playlists(name_filter="הלכה יומית")
    assert len(playlists) > 0
    
    # Get videos from first playlist
    first_playlist = playlists[0]
    videos = service.get_playlist_videos(first_playlist['id'])
    
    # Should have at least one video
    assert len(videos) > 0
    
    # Each video should have required fields
    for video in videos:
        assert 'video_id' in video
        assert 'url' in video
        assert 'description' in video
        assert video['url'].startswith('https://www.youtube.com/watch?v=')


def test_get_videos_from_filtered_playlists():
    """Test getting all videos from filtered playlists."""
    service = YouTubeService()
    videos = service.get_videos_from_filtered_playlists("הלכה יומית")
    
    # Should have many videos (we know there are 1000+)
    assert len(videos) > 100
    
    # Verify video structure
    sample_video = videos[0]
    assert 'video_id' in sample_video
    assert 'url' in sample_video
    assert 'published_at' in sample_video


# Standalone script mode for manual testing
if __name__ == "__main__":
    print("Testing YouTube API connectivity...\n")
    
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
