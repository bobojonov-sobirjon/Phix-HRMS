"""add_profile_views_manual

Revision ID: add_profile_views_manual
Revises: add_saved_jobs_manual
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_profile_views_manual'
down_revision: Union[str, Sequence[str], None] = 'add_saved_jobs_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Stub migration - database is already at this state."""
    # This is a placeholder migration file for a migration that was deleted
    # The database is already at this revision, so no changes are needed
    pass


def downgrade() -> None:
    """Stub migration - no changes needed."""
    pass

