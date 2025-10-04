"""add_transcripts_table

Revision ID: 744d231300b3
Revises: a945124197ab
Create Date: 2025-10-04 22:57:24.220674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '744d231300b3'
down_revision: Union[str, Sequence[str], None] = 'a945124197ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'transcripts',
        sa.Column('video_id', sa.String(20), sa.ForeignKey('videos.video_id', ondelete='CASCADE'), primary_key=True, comment='YouTube video ID (FK to videos)'),
        sa.Column('source', sa.String(20), nullable=False, comment='Transcript source: youtube or whisper'),
        sa.Column('language', sa.String(10), nullable=True, comment='Transcript language code (e.g., he, en)'),
        sa.Column('full_text', sa.Text, nullable=False, comment='Complete transcript text'),
        sa.Column('segments', postgresql.JSONB, nullable=True, comment='Transcript segments with timestamps'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='Record last update timestamp'),
    )
    
    # Create index on source for filtering
    op.create_index('ix_transcripts_source', 'transcripts', ['source'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_transcripts_source', table_name='transcripts')
    op.drop_table('transcripts')
