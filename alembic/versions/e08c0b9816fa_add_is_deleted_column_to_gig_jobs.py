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
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_deleted column to gig_jobs table
    op.add_column('gig_jobs', sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_deleted column from gig_jobs table
    op.drop_column('gig_jobs', 'is_deleted')
