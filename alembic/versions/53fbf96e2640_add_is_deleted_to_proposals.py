"""add_is_deleted_to_proposals

Revision ID: 53fbf96e2640
Revises: e08c0b9816fa
Create Date: 2025-09-22 12:10:43.519503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53fbf96e2640'
down_revision: Union[str, Sequence[str], None] = '24d36116cb81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_deleted column to proposals table
    op.add_column('proposals', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_deleted column from proposals table
    op.drop_column('proposals', 'is_deleted')
