"""Add tags and taggings tables

Revision ID: h2k3l4addtags
Revises: g7h8i9addembed
Create Date: 2025-10-06 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h2k3l4addtags'
down_revision: Union[str, Sequence[str], None] = 'g7h8i9addembed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create tags and taggings."""
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True, comment='Tag primary key'),
        sa.Column('name', sa.String(length=20), nullable=False, comment='Human-readable tag name (max 20 chars)'),
        sa.Column('description', sa.Text(), nullable=True, comment='Optional description for the tag'),
        sa.Column('type', sa.String(length=30), nullable=False, comment="Tag type: 'date' | 'manual' | 'automatic'"),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
    )

    # unique constraint on name alone
    op.create_unique_constraint('uq_tags_name', 'tags', ['name'])
    op.create_index('ix_tags_type', 'tags', ['type'])

    op.create_table(
        'taggings',
        sa.Column('id', sa.Integer(), primary_key=True, comment='Tagging primary key'),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), nullable=False, comment='FK to tags'),
        sa.Column('video_id', sa.String(length=20), sa.ForeignKey('videos.video_id', ondelete='CASCADE'), nullable=False, comment='FK to videos'),
        sa.Column('source', sa.String(length=100), nullable=True, comment='Source or method that created this tagging'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_unique_constraint('uq_taggings_tag_video', 'taggings', ['tag_id', 'video_id'])
    op.create_index('ix_taggings_tag_video', 'taggings', ['tag_id', 'video_id'])


def downgrade() -> None:
    """Downgrade schema: drop taggings and tags."""
    op.drop_index('ix_taggings_tag_video', table_name='taggings')
    op.drop_constraint('uq_taggings_tag_video', 'taggings', type_='unique')
    op.drop_table('taggings')

    op.drop_index('ix_tags_type', table_name='tags')
    op.drop_constraint('uq_tags_name', 'tags', type_='unique')
    op.drop_table('tags')
