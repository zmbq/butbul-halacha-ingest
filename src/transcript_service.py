"""
Service for fetching video transcripts from various sources.
"""

import os
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
import yt_dlp
from openai import OpenAI
from src.config import config


class TranscriptService:
    """Service for fetching transcripts from YouTube and other sources."""
    
    def __init__(self, openai_api_key: str | None = None):
        """Initialize the transcript service."""
        self.api = YouTubeTranscriptApi()
        self.openai_client = OpenAI(api_key=openai_api_key or config.openai_api_key)

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

    def transcribe_with_whisper(self, video_id: str, youtube_url: str, temp_dir: Path | None = None) -> Optional[Dict]:
        """
        Transcribe a YouTube video using OpenAI's Whisper API.
        
        Steps:
        1. Download audio from YouTube using yt-dlp
        2. Send audio to Whisper API
        3. Get transcript with timestamps
        4. Clean up audio file
        
        Args:
            video_id: YouTube video ID
            youtube_url: Full YouTube URL
            temp_dir: Optional temporary directory for audio files (default: system temp)
            
        Returns:
            Dictionary with transcript data or None if failed
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir()) / "butbul_audio"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        audio_file_path = None
        
        try:
            # Step 1: Download audio using yt-dlp
            audio_file_path = temp_dir / f"{video_id}.mp3"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(temp_dir / f"{video_id}.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
            }
            
            print(f"  Downloading audio from YouTube...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            if not audio_file_path.exists():
                print(f"  ✗ Audio file not found after download: {audio_file_path}")
                return None
            
            file_size_mb = audio_file_path.stat().st_size / (1024 * 1024)
            print(f"  ✓ Audio downloaded ({file_size_mb:.1f} MB)")
            
            # Step 2: Check file size (Whisper API has 25 MB limit)
            if file_size_mb > 25:
                print(f"  ✗ Audio file too large ({file_size_mb:.1f} MB > 25 MB limit)")
                print(f"  TODO: Implement chunking for large files")
                return None
            
            # Step 3: Transcribe with Whisper API
            print(f"  Sending to Whisper API (this may take a while)...")
            start_time = time.time()
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript_response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="he",  # Hebrew
                    response_format="verbose_json",  # Get timestamps
                    timestamp_granularities=["segment"]
                )
            
            elapsed_time = time.time() - start_time
            print(f"  ✓ Transcription complete (took {elapsed_time:.1f}s)")
            
            # Step 4: Process response
            full_text = transcript_response.text
            language = transcript_response.language or "he"
            
            # Convert segments to our format
            segments_dict = []
            if hasattr(transcript_response, 'segments') and transcript_response.segments:
                for segment in transcript_response.segments:
                    segments_dict.append({
                        'text': segment.text,
                        'start': segment.start,
                        'duration': segment.end - segment.start
                    })
            
            return {
                'video_id': video_id,
                'source': 'whisper',
                'language': language,
                'full_text': full_text,
                'segments': segments_dict
            }
            
        except Exception as e:
            print(f"  ✗ Error transcribing with Whisper: {e}")
            return None
            
        finally:
            # Clean up audio file
            if audio_file_path and audio_file_path.exists():
                try:
                    audio_file_path.unlink()
                    print(f"  ✓ Cleaned up audio file")
                except Exception as e:
                    print(f"  ⚠ Warning: Could not delete audio file: {e}")


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
