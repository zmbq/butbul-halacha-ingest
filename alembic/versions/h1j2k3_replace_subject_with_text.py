"""Replace subject/extra_text with single text column in embeddings

Revision ID: h1j2k3replace
Revises: g7h8i9addembed
Create Date: 2025-10-06 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h1j2k3replace'
down_revision: Union[str, Sequence[str], None] = 'g7h8i9addembed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new text column (nullable for migration safety)
    op.add_column('embeddings', sa.Column('text', sa.Text(), nullable=True, comment='Full text used to create this embedding'))

    # Replace the existing check constraint to only require chunk embeddings to have a chunk id
    op.drop_constraint('ck_embeddings_kind_fields', 'embeddings', type_='check')
    op.create_check_constraint('ck_embeddings_kind_fields', 'embeddings', "(kind != 'chunk' OR transcription_chunk_id IS NOT NULL)")

    # Optionally migrate existing subject/extra_text into text (best-effort)
    op.execute("""
    UPDATE embeddings
    SET text = COALESCE(subject, '') || CASE WHEN extra_text IS NOT NULL AND extra_text <> '' THEN ' ' || extra_text ELSE '' END
    WHERE subject IS NOT NULL OR extra_text IS NOT NULL;
    """
    )

    # Drop old columns
    op.drop_column('embeddings', 'subject')
    op.drop_column('embeddings', 'extra_text')


def downgrade() -> None:
    # Recreate subject & extra_text, then remove text and restore old check constraint
    op.add_column('embeddings', sa.Column('subject', sa.String(length=500), nullable=True))
    op.add_column('embeddings', sa.Column('extra_text', sa.Text(), nullable=True))

    # Try to split text back into subject/extra_text (best-effort: subject gets first 500 chars)
    op.execute("""
    UPDATE embeddings
    SET subject = CASE WHEN text IS NOT NULL THEN substring(text from 1 for 500) ELSE NULL END,
        extra_text = NULL
    WHERE text IS NOT NULL;
    """
    )

    op.drop_constraint('ck_embeddings_kind_fields', 'embeddings', type_='check')
    op.create_check_constraint('ck_embeddings_kind_fields', 'embeddings', "(kind != 'chunk' OR transcription_chunk_id IS NOT NULL) AND (kind != 'subject' OR subject IS NOT NULL)")

    op.drop_column('embeddings', 'text')
