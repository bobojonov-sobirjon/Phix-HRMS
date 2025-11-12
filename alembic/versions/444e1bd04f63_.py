"""empty message

Revision ID: 444e1bd04f63
Revises: 2acd05c72b2f
Create Date: 2025-11-12 16:31:23.778723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '444e1bd04f63'
down_revision: Union[str, Sequence[str], None] = '2acd05c72b2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
