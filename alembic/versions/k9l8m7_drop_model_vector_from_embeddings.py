"""Drop model and vector columns from embeddings

Revision ID: k9l8m7_drop_model_vector
Revises: j4k5l6_makecachenonnull
Create Date: 2025-10-06 12:30:00.000000

This migration removes the duplicated `model` and `vector` columns from the
`embeddings` table. The canonical `model` and `vector` remain in
`embeddings_cache` and `embeddings.source_cache_id` references the canonical
row.

If you have existing data you want to preserve, back it up before running this
migration. The project previously ensured `embeddings` was empty before
normalizing, so this should be safe in that environment.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k9l8m7_drop_model_vector'
down_revision = 'j4k5l6makecachenonnull'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the columns in a batch alter to support SQLite if used in tests.
    with op.batch_alter_table('embeddings') as batch_op:
        # If the columns don't exist (older schema), these operations will fail;
        # we intentionally keep straightforward SQL here and expect the
        # environment to be on the matching revision chain.
        batch_op.drop_column('vector')
        batch_op.drop_column('model')


def downgrade() -> None:
    # Recreate the columns (best-effort). This will restore the columns but
    # not repopulate data.
    with op.batch_alter_table('embeddings') as batch_op:
        batch_op.add_column(sa.Column('model', sa.String(length=128), nullable=False))
        # Recreate vector as float[] fallback; if you use pgvector in prod,
        # adjust the type accordingly.
        try:
            from pgvector.sqlalchemy import Vector  # type: ignore
            vec_type = Vector(1536)
        except Exception:
            vec_type = sa.ARRAY(sa.Float)
        batch_op.add_column(sa.Column('vector', vec_type, nullable=False))
