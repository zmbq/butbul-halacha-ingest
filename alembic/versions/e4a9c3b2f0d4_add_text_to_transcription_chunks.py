"""add text column to transcription_chunks

Revision ID: e4a9c3b2f0d4
Revises: d2f3b7c1e9a1
Create Date: 2025-10-06 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e4a9c3b2f0d4'
down_revision = 'd2f3b7c1e9a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('transcription_chunks', sa.Column('text', sa.Text(), nullable=False, server_default=''))
    # remove server default to avoid affecting future inserts
    op.alter_column('transcription_chunks', 'text', server_default=None)


def downgrade():
    op.drop_column('transcription_chunks', 'text')
