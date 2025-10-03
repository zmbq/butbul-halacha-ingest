"""
YouTube API service for fetching playlists and videos.
"""

from typing import List, Dict, Optional
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import config


class YouTubeService:
    """Service for interacting with YouTube Data API v3."""

    def __init__(self, api_key: Optional[str] = None, channel_id: Optional[str] = None):
        """
        Initialize YouTube service.

        Args:
            api_key: YouTube API key (defaults to config.youtube_api_key)
            channel_id: YouTube channel ID (defaults to config.youtube_channel_id)
        """
        self.api_key = api_key or config.youtube_api_key
        self.channel_id = channel_id or config.youtube_channel_id
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)

    def get_playlists(self, name_filter: Optional[str] = None) -> List[Dict]:
        """
        Get all playlists from the channel.

        Args:
            name_filter: Optional string to filter playlist names (case-insensitive)

        Returns:
            List of playlist dictionaries with 'id', 'title', and 'description'
        """
        playlists = []
        next_page_token = None

        try:
            while True:
                request = self.youtube.playlists().list(
                    part='snippet,contentDetails',
                    channelId=self.channel_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    playlist_data = {
                        'id': item['id'],
                        'title': item['snippet']['title'],
                        'description': item['snippet'].get('description', ''),
                        'item_count': item['contentDetails'].get('itemCount', 0)
                    }

                    # Apply filter if provided
                    if name_filter:
                        if name_filter.lower() in playlist_data['title'].lower():
                            playlists.append(playlist_data)
                    else:
                        playlists.append(playlist_data)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            print(f"Found {len(playlists)} playlists" + 
                  (f" matching '{name_filter}'" if name_filter else ""))
            return playlists

        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            raise

    def get_playlist_videos(self, playlist_id: str) -> List[Dict]:
        """
        Get all videos from a specific playlist.

        Args:
            playlist_id: YouTube playlist ID

        Returns:
            List of video dictionaries with 'video_id', 'url', 'description', 'published_at'
        """
        videos = []
        next_page_token = None

        try:
            while True:
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    
                    # Parse published date
                    published_at = None
                    if 'publishedAt' in snippet:
                        try:
                            published_at = datetime.fromisoformat(
                                snippet['publishedAt'].replace('Z', '+00:00')
                            )
                        except ValueError:
                            pass

                    video_data = {
                        'video_id': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'description': snippet.get('description', ''),
                        'published_at': published_at,
                        'title': snippet.get('title', '')
                    }
                    videos.append(video_data)

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            print(f"Found {len(videos)} videos in playlist {playlist_id}")
            return videos

        except HttpError as e:
            print(f"An HTTP error occurred: {e}")
            raise

    def get_videos_from_filtered_playlists(self, playlist_name_filter: str) -> List[Dict]:
        """
        Get all videos from playlists matching the given name filter.

        Args:
            playlist_name_filter: String to filter playlist names

        Returns:
            List of all videos from matching playlists
        """
        print(f"Searching for playlists containing '{playlist_name_filter}'...")
        playlists = self.get_playlists(name_filter=playlist_name_filter)

        all_videos = []
        for playlist in playlists:
            print(f"\nProcessing playlist: {playlist['title']} ({playlist['item_count']} items)")
            videos = self.get_playlist_videos(playlist['id'])
            all_videos.extend(videos)

        print(f"\nTotal videos found: {len(all_videos)}")
        return all_videos


if __name__ == "__main__":
    # Test the YouTube service
    service = YouTubeService()
    
    # Test getting playlists
    print("Testing playlist retrieval...")
    playlists = service.get_playlists(name_filter="הלכה יומית")
    
    for playlist in playlists:
        print(f"- {playlist['title']} (ID: {playlist['id']}, Videos: {playlist['item_count']})")
