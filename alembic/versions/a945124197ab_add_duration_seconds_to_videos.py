"""add_duration_seconds_to_videos

Revision ID: a945124197ab
Revises: 5cdf4eb091b7
Create Date: 2025-10-04 22:48:07.605271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a945124197ab'
down_revision: Union[str, Sequence[str], None] = '5cdf4eb091b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('videos', sa.Column('duration_seconds', sa.Integer(), nullable=True, comment='Video duration in seconds'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('videos', 'duration_seconds')
