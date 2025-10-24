"""add_is_deleted_column_to_gig_jobs

Revision ID: e08c0b9816fa
Revises: affb6917a172
Create Date: 2025-09-22 12:08:48.345769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e08c0b9816fa'
down_revision: Union[str, Sequence[str], None] = 'e17310649136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # is_deleted column is already included in the gig_jobs table creation
    # This migration is kept for historical purposes but does nothing
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # is_deleted column is part of the table creation, so no need to drop it here
    pass
