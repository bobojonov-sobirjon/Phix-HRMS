"""Merge manual heads

Revision ID: merge_manual_heads
Revises: add_user_categories_manual, add_is_deleted_manual, add_profile_views_manual
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'merge_manual_heads'
down_revision: Union[str, Sequence[str], None] = ('add_user_categories_manual', 'add_is_deleted_manual', 'add_profile_views_manual')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge the two manual heads."""
    # This is a merge migration - no schema changes needed
    # The database is already at add_user_categories_manual
    # We just need to mark this merge as applied
    pass


def downgrade() -> None:
    """Downgrade merge."""
    # This is a merge migration - no schema changes to reverse
    pass
