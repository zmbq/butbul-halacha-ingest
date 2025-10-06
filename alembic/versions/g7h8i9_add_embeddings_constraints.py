"""Add constraints and indexes for embeddings

Revision ID: g7h8i9addembed
Revises: f1a2b3c4d5e6
Create Date: 2025-10-06 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9addembed'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add a check constraint to ensure when kind='chunk' there's a chunk id,
    # and when kind='subject' there's a subject text. This prevents storing
    # incomplete embeddings rows.
    op.create_check_constraint(
        'ck_embeddings_kind_fields',
        'embeddings',
        "(kind != 'chunk' OR transcription_chunk_id IS NOT NULL) AND (kind != 'subject' OR subject IS NOT NULL)"
    )

    # Create a unique partial index so there can't be two embeddings for the
    # same chunk+model (useful to avoid duplicates when running the pipeline).
    op.create_index(
        'uq_embeddings_chunk_model',
        'embeddings',
        ['transcription_chunk_id', 'model'],
        unique=True,
        postgresql_where=sa.text('transcription_chunk_id IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('uq_embeddings_chunk_model', table_name='embeddings')
    op.drop_constraint('ck_embeddings_kind_fields', 'embeddings', type_='check')
