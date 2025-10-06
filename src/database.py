"""
Database models and connection management.
"""

from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey, Float, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from src.config import config

# Create base class for declarative models
Base = declarative_base()


class Video(Base):
    """Model for storing YouTube video metadata."""

    __tablename__ = "videos"

    # YouTube video ID is the primary key
    video_id = Column(String(20), primary_key=True, comment="YouTube video ID")
    
    # Video URL
    url = Column(String(255), nullable=False, comment="Full YouTube video URL")
    
    # Video title
    title = Column(String(255), nullable=False, comment="Video title from YouTube")
    
    # Video description
    description = Column(Text, nullable=True, comment="Video description from YouTube")
    
    # Published date (when video was published, not uploaded)
    published_at = Column(DateTime, nullable=True, comment="Video publish date")
    
    # Video duration in seconds
    duration_seconds = Column(Integer, nullable=True, comment="Video duration in seconds")
    
    # Metadata timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="Record last update timestamp")

    def __repr__(self):
        return f"<Video(video_id='{self.video_id}', url='{self.url}', published_at='{self.published_at}')>"


class VideoMetadata(Base):
    """Model for storing extracted metadata from video titles and descriptions."""

    __tablename__ = "video_metadata"

    # Foreign key to videos table
    video_id = Column(String(20), primary_key=True, comment="YouTube video ID (FK to videos)")
    
    # Extracted Hebrew date from title/description
    hebrew_date = Column(String(50), nullable=True, comment="Hebrew date extracted from title (e.g., 'ג' תשרי התשפ\"ו')")
    
    # Day of week extracted from Hebrew date
    day_of_week = Column(String(20), nullable=True, comment="Day of week in Hebrew (e.g., 'ג'', 'ד'', 'ה'')")
    
    # Extracted subject/topic from title/description
    subject = Column(String(500), nullable=True, comment="Subject/topic extracted from title")
    
    # Metadata timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="Record last update timestamp")

    def __repr__(self):
        return f"<VideoMetadata(video_id='{self.video_id}', hebrew_date='{self.hebrew_date}', subject='{self.subject[:50]}...')>"


class Transcript(Base):
    """Model for storing video transcripts from various sources."""

    __tablename__ = "transcripts"

    # Foreign key to videos table
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), primary_key=True, comment="YouTube video ID (FK to videos)")
    
    # Transcript source (youtube, whisper, etc.)
    source = Column(String(20), nullable=False, comment="Transcript source: youtube or whisper")
    
    # Language code
    language = Column(String(10), nullable=True, comment="Transcript language code (e.g., he, en)")
    
    # Full transcript text
    full_text = Column(Text, nullable=False, comment="Complete transcript text")
    
    # Segments with timestamps (JSONB for flexibility)
    segments = Column(JSONB, nullable=True, comment="Transcript segments with timestamps")
    
    # Metadata timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="Record last update timestamp")

    def __repr__(self):
        return f"<Transcript(video_id='{self.video_id}', source='{self.source}', language='{self.language}')>"


class TranscriptionSegment(Base):
    """Model for storing individual transcript segments (from Whisper or other sources).

    Each row represents a single contiguous segment with start time, duration, and text.
    This table is intended to be used for embedding generation and quick time-based queries.
    """

    __tablename__ = "transcription_segments"

    # Auto-incrementing primary key for the segment
    id = Column(Integer, primary_key=True, comment="Segment primary key")

    # Reference to the video this segment belongs to. Cascade on video delete.
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True, comment="YouTube video ID (FK to videos)")

    # Source of the transcript (whisper, youtube, etc.)
    source = Column(String(20), nullable=False, default='whisper', comment="Transcript source: whisper, youtube, etc.")

    # Order of the segment within the transcript (0-based)
    segment_index = Column(Integer, nullable=False, comment="Index/order of the segment within the transcript")

    # Segment timing: start (seconds), duration (seconds), and end (seconds)
    start = Column(Float, nullable=False, comment="Segment start time in seconds")
    duration = Column(Float, nullable=False, comment="Segment duration in seconds")
    end = Column(Float, nullable=False, comment="Segment end time in seconds (start + duration)")

    # Transcribed text for this segment
    text = Column(Text, nullable=False, comment="Transcript text for the segment")

    # Raw segment JSON for any additional Whisper fields (tokens, confidence, etc.)
    raw = Column(JSONB, nullable=True, comment="Raw segment JSON from the transcription service")

    # Timestamps for record management
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="Record last update timestamp")

    __table_args__ = (
        # Index to support queries by video and start time
        Index('ix_transcription_segments_video_start', 'video_id', 'start'),
        # Uniqueness to prevent duplicate inserts for same video/segment index/source
        UniqueConstraint('video_id', 'source', 'segment_index', name='uq_transcription_segments_video_source_index'),
    )

    def __repr__(self):
        return f"<TranscriptionSegment(id={self.id}, video_id='{self.video_id}', index={self.segment_index}, start={self.start})>"


class TranscriptionChunk(Base):
    """Model for storing contiguous chunks of transcription segments used for embeddings.

    Each chunk covers a contiguous range of segments (first_segment_id .. last_segment_id)
    and represents approximately 20-30 seconds of audio. Chunks may overlap by one
    segment with the previous chunk to provide context.
    """

    __tablename__ = "transcription_chunks"

    # Auto-incrementing primary key
    id = Column(Integer, primary_key=True, comment="Chunk primary key")

    # Reference to the video this chunk belongs to
    video_id = Column(String(20), ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, index=True, comment="YouTube video ID (FK to videos)")

    # Transcript source (whisper, youtube, etc.)
    source = Column(String(20), nullable=False, default='whisper', comment="Transcript source: whisper, youtube, etc.")

    # First and last segment IDs (inclusive) that make up this chunk
    first_segment_id = Column(Integer, ForeignKey('transcription_segments.id', ondelete='CASCADE'), nullable=False, comment="First segment id in this chunk (inclusive)")
    last_segment_id = Column(Integer, ForeignKey('transcription_segments.id', ondelete='CASCADE'), nullable=False, comment="Last segment id in this chunk (inclusive)")

    # Optional human-readable boundaries (start/end seconds) cached for quick queries
    start = Column(Float, nullable=True, comment="Chunk start time in seconds (from first segment)")
    end = Column(Float, nullable=True, comment="Chunk end time in seconds (from last segment)")
    # Aggregated text for this chunk (concatenation of segment texts)
    text = Column(Text, nullable=False, default='', comment="Aggregated text for chunk (concatenated segment texts)")

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="Record last update timestamp")

    __table_args__ = (
        UniqueConstraint('video_id', 'first_segment_id', 'last_segment_id', name='uq_transcription_chunks_video_first_last'),
        Index('ix_transcription_chunks_video_start_end', 'video_id', 'start', 'end'),
    )

    def __repr__(self):
        return f"<TranscriptionChunk(id={self.id}, video_id='{self.video_id}', first={self.first_segment_id}, last={self.last_segment_id})>"


# Database engine and session factory
engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)




def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


# Note: database schema changes should be done via Alembic migrations.
