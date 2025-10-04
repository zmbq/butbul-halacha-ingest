"""
Database models and connection management.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record last update timestamp")

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record last update timestamp")

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record last update timestamp")

    def __repr__(self):
        return f"<Transcript(video_id='{self.video_id}', source='{self.source}', language='{self.language}')>"


# Database engine and session factory
engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all tables.
    
    NOTE: This is for initial setup only. For schema changes after initial
    deployment, use Alembic migrations instead. See MIGRATIONS.md for details.
    
    To create migrations after modifying this file:
        poetry run alembic revision --autogenerate -m "Description"
        poetry run alembic upgrade head
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def drop_all_tables():
    """Drop all tables. WARNING: This will delete all data!"""
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped successfully.")


def recreate_db():
    """Drop and recreate all tables. WARNING: This will delete all data!"""
    print("Dropping all tables...")
    drop_all_tables()
    print("Creating all tables...")
    init_db()
    print("Database recreated successfully.")


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


if __name__ == "__main__":
    # Recreate tables when run directly (drops and recreates)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--recreate":
        recreate_db()
    else:
        init_db()
