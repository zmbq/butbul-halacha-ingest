"""create embeddings cache and embeddings tables

Revision ID: f1a2b3c4d5e6
Revises: e4a9c3b2f0d4
Create Date: 2025-10-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e4a9c3b2f0d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use pgvector for efficient vector storage & kNN queries.
    # Assumption: using OpenAI `text-embedding-3-small` with vector dimension 1536.
    # If you use a different model with a different dimension, update the dimension
    # here and in the SQLAlchemy model definitions.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Create tables using the native `vector` type with fixed dimension
    op.execute(
        """
        CREATE TABLE embeddings_cache (
            id serial PRIMARY KEY,
            text text NOT NULL,
            model varchar(128) NOT NULL,
            vector vector(1536) NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL
        );
        """
    )

    op.execute(
        """
        CREATE TABLE embeddings (
            id serial PRIMARY KEY,
            video_id varchar(20) REFERENCES videos(video_id) ON DELETE CASCADE,
            transcription_chunk_id integer REFERENCES transcription_chunks(id) ON DELETE CASCADE,
            kind varchar(50) NOT NULL,
            subject varchar(500),
            extra_text text,
            model varchar(128) NOT NULL,
            vector vector(1536) NOT NULL,
            source_cache_id integer REFERENCES embeddings_cache(id) ON DELETE SET NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz NOT NULL
        );
        """
    )

    # Indexes to speed up lookups
    op.create_index('ix_embeddings_kind_video_chunk', 'embeddings', ['kind', 'video_id', 'transcription_chunk_id'])
    op.create_index('ix_embeddings_cache_text_model', 'embeddings_cache', ['text', 'model'])


def downgrade() -> None:
    op.drop_index('ix_embeddings_cache_text_model', table_name='embeddings_cache')
    op.drop_index('ix_embeddings_kind_video_chunk', table_name='embeddings')
    op.drop_table('embeddings')
    op.drop_table('embeddings_cache')
