"""
Service for fetching video transcripts from various sources.
"""

from typing import Optional, Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)


class TranscriptService:
    """Service for fetching transcripts from YouTube and other sources."""
    
    def __init__(self):
        """Initialize the transcript service."""
        self.api = YouTubeTranscriptApi()

    def fetch_youtube_transcript(self, video_id: str, languages: List[str] | None = None) -> Optional[Dict]:
        """
        Fetch transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages list (e.g., ['he', 'iw', 'en']). 
                      If None, fetches any available transcript.
        
        Returns:
            Dictionary with transcript data:
            {
                'video_id': str,
                'source': 'youtube',
                'language': str,
                'full_text': str,
                'segments': list of {'text': str, 'start': float, 'duration': float}
            }
            Returns None if transcript is not available.
        """
        if languages is None:
            # Default: prefer Hebrew (he/iw are both Hebrew codes), then English
            languages = ['he', 'iw', 'en']
        
        try:
            # Fetch transcript (automatically picks first available language from the list)
            transcript_list = self.api.list(video_id)
            
            # Try to get transcript in preferred language
            transcript = None
            language_code = None
            
            # First try manually generated transcripts
            for lang in languages:
                try:
                    transcript = transcript_list.find_manually_created_transcript([lang])
                    language_code = transcript.language_code
                    break
                except NoTranscriptFound:
                    continue
            
            # If no manual transcript, try auto-generated
            if transcript is None:
                for lang in languages:
                    try:
                        transcript = transcript_list.find_generated_transcript([lang])
                        language_code = transcript.language_code
                        break
                    except NoTranscriptFound:
                        continue
            
            # If still no transcript, get any available transcript
            if transcript is None:
                try:
                    # Try to get any available transcript
                    for t in transcript_list:
                        transcript = t
                        language_code = t.language_code
                        break
                except:
                    pass
            
            if transcript is None:
                return None
            
            # Fetch the actual transcript data
            fetched_transcript = transcript.fetch()
            segments = fetched_transcript.snippets
            
            # Build full text from segments
            full_text = ' '.join(segment.text for segment in segments)
            
            # Convert segments to dict format for JSON storage
            segments_dict = [
                {
                    'text': segment.text,
                    'start': segment.start,
                    'duration': segment.duration
                }
                for segment in segments
            ]
            
            return {
                'video_id': video_id,
                'source': 'youtube',
                'language': language_code,
                'full_text': full_text,
                'segments': segments_dict  # List of {'text': str, 'start': float, 'duration': float}
            }
            
        except TranscriptsDisabled:
            # Transcripts are disabled for this video
            return None
        except NoTranscriptFound:
            # No transcript found in any language
            return None
        except VideoUnavailable:
            # Video does not exist or is private
            return None
        except Exception as e:
            # Catch any other errors (including rate limiting, unavailable transcripts, etc.)
            print(f"Unexpected error fetching transcript for {video_id}: {e}")
            return None


if __name__ == "__main__":
    # Test the transcript service
    service = TranscriptService()
    
    # Test with a known video (replace with actual video ID)
    test_video_id = "3pCxWIdvpFA"  # First video from your collection
    print(f"Testing transcript fetch for video: {test_video_id}")
    
    result = service.fetch_youtube_transcript(test_video_id)
    
    if result:
        print(f"\n✓ Transcript found!")
        print(f"  Language: {result['language']}")
        print(f"  Source: {result['source']}")
        print(f"  Segments: {len(result['segments'])}")
        print(f"  Text length: {len(result['full_text'])} characters")
        print(f"  First 200 chars: {result['full_text'][:200]}...")
    else:
        print("\n✗ No transcript available for this video")
