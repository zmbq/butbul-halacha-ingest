"""alter timestamps to timestamptz

Revision ID: b3f1c9d2e7a8
Revises: 91cf6fe6caa1
Create Date: 2025-10-06 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f1c9d2e7a8'
down_revision = '91cf6fe6caa1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert columns to TIMESTAMP WITH TIME ZONE on PostgreSQL
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect != 'postgresql':
        # Only apply on PostgreSQL
        return

    # videos: created_at, updated_at, published_at (if present)
    op.execute("ALTER TABLE videos ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE videos ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE videos ALTER COLUMN published_at TYPE TIMESTAMP WITH TIME ZONE USING published_at AT TIME ZONE 'UTC'")

    # video_metadata
    op.execute("ALTER TABLE video_metadata ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE video_metadata ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")

    # transcripts
    op.execute("ALTER TABLE transcripts ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transcripts ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")

    # transcription_segments
    op.execute("ALTER TABLE transcription_segments ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transcription_segments ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    conn = op.get_bind()
    dialect = conn.dialect.name
    if dialect != 'postgresql':
        return

    # Revert to TIMESTAMP WITHOUT TIME ZONE (naive)
    op.execute("ALTER TABLE videos ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE videos ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE videos ALTER COLUMN published_at TYPE TIMESTAMP WITHOUT TIME ZONE USING published_at AT TIME ZONE 'UTC'")

    op.execute("ALTER TABLE video_metadata ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE video_metadata ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")

    op.execute("ALTER TABLE transcripts ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transcripts ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")

    op.execute("ALTER TABLE transcription_segments ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE transcription_segments ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE USING updated_at AT TIME ZONE 'UTC'")
