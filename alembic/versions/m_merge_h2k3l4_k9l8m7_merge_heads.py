"""Merge heads h2k3l4addtags and k9l8m7_drop_model_vector

Revision ID: m_merge_h2k3l4_k9l8m7
Revises: h2k3l4addtags, k9l8m7_drop_model_vector
Create Date: 2025-10-06 13:05:00.000000

This is a merge migration that unifies two separate heads into a single
revision. It performs no schema changes; it's intended to resolve the
"multiple heads" error and keep Alembic's history linear for upgrades.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm_merge_h2k3l4_k9l8m7'
down_revision: Union[str, Sequence[str], None] = ('h2k3l4addtags', 'k9l8m7_drop_model_vector')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge-only migration: no schema changes.
    pass


def downgrade() -> None:
    # Can't sensibly 'un-merge' automatically.
    pass
