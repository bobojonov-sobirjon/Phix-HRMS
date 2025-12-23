"""merge_heads

Revision ID: b6ad4cbff0fa
Revises: b54df9e3739c
Create Date: 2025-12-23 22:41:31.428018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6ad4cbff0fa'
down_revision: Union[str, Sequence[str], None] = 'b54df9e3739c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
