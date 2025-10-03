"""
Database models and connection management.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import config

# Create base class for declarative models
Base = declarative_base()


class Video(Base):
    """Model for storing YouTube video metadata."""

    __tablename__ = "videos"

    # YouTube video ID is the primary key
    video_id = Column(String(20), primary_key=True, comment="YouTube video ID")
    
    # Video URL
    url = Column(String(255), nullable=False, comment="Full YouTube video URL")
    
    # Video description
    description = Column(Text, nullable=True, comment="Video description from YouTube")
    
    # Published date (when video was published, not uploaded)
    published_at = Column(DateTime, nullable=True, comment="Video publish date")
    
    # Metadata timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Record creation timestamp")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Record last update timestamp")

    def __repr__(self):
        return f"<Video(video_id='{self.video_id}', url='{self.url}', published_at='{self.published_at}')>"


# Database engine and session factory
engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


def get_db():
    """Get a database session."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Session will be closed by caller


if __name__ == "__main__":
    # Create tables when run directly
    init_db()
