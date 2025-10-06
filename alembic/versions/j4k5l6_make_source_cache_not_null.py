"""Make embeddings.source_cache_id NOT NULL and remove text column

Revision ID: j4k5l6makecachenonnull
Revises: h1j2k3replace
Create Date: 2025-10-06 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j4k5l6makecachenonnull'
down_revision: Union[str, Sequence[str], None] = 'h1j2k3replace'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # For rows where source_cache_id is null, try to find a matching cache row by text & model
    # and set source_cache_id accordingly. This is best-effort; if no cache row exists
    # the source_cache_id will remain NULL and migration will fail when altering to NOT NULL.
    op.execute(
        """
        UPDATE embeddings e
        SET source_cache_id = c.id
        FROM embeddings_cache c
        WHERE e.source_cache_id IS NULL
          AND e.text IS NOT NULL
          AND c.text = e.text
          AND c.model = e.model;
        """
    )

    # Now drop the text column
    with op.batch_alter_table('embeddings') as batch_op:
        batch_op.drop_column('text')

    # Alter source_cache_id to NOT NULL
    with op.batch_alter_table('embeddings') as batch_op:
        batch_op.alter_column('source_cache_id', nullable=False)


def downgrade() -> None:
    # revert: add text column back (nullable)
    with op.batch_alter_table('embeddings') as batch_op:
        batch_op.add_column(sa.Column('text', sa.Text(), nullable=True))
        batch_op.alter_column('source_cache_id', nullable=True)
