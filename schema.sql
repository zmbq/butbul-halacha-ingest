-- Database schema for Butbul Halacha Ingest
-- PostgreSQL SQL script to create the videos table

-- Drop table if exists (use with caution!)
-- DROP TABLE IF EXISTS videos;

-- Create videos table
CREATE TABLE IF NOT EXISTS videos (
    -- Primary key: YouTube video ID
    video_id VARCHAR(20) PRIMARY KEY,
    
    -- Video URL
    url VARCHAR(255) NOT NULL,
    
    -- Video description from YouTube
    description TEXT,
    
    -- Published date (when video was published on YouTube)
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Add comments to table and columns
COMMENT ON TABLE videos IS 'YouTube videos from הלכה יומית playlists';
COMMENT ON COLUMN videos.video_id IS 'YouTube video ID (unique identifier)';
COMMENT ON COLUMN videos.url IS 'Full YouTube video URL';
COMMENT ON COLUMN videos.description IS 'Video description from YouTube';
COMMENT ON COLUMN videos.published_at IS 'Video publish date from YouTube';
COMMENT ON COLUMN videos.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN videos.updated_at IS 'Record last update timestamp';

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_videos_published_at ON videos(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);

-- Create a trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_videos_updated_at ON videos;
CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON videos TO your_app_user;
