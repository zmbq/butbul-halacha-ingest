"""create transcription_chunks table

Revision ID: d2f3b7c1e9a1
Revises: b3f1c9d2e7a8
Create Date: 2025-10-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd2f3b7c1e9a1'
down_revision = 'b3f1c9d2e7a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'transcription_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('video_id', sa.String(length=20), sa.ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('first_segment_id', sa.Integer(), sa.ForeignKey('transcription_segments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('last_segment_id', sa.Integer(), sa.ForeignKey('transcription_segments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start', sa.Float(), nullable=True),
        sa.Column('end', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_transcription_chunks_video_start_end', 'transcription_chunks', ['video_id', 'start', 'end'])
    op.create_unique_constraint('uq_transcription_chunks_video_first_last', 'transcription_chunks', ['video_id', 'first_segment_id', 'last_segment_id'])


def downgrade():
    op.drop_constraint('uq_transcription_chunks_video_first_last', 'transcription_chunks', type_='unique')
    op.drop_index('ix_transcription_chunks_video_start_end', table_name='transcription_chunks')
    op.drop_table('transcription_chunks')
