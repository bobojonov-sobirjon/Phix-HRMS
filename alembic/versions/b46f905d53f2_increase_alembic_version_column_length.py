"""increase_alembic_version_column_length

Revision ID: b46f905d53f2
Revises: 90475e75a94f
Create Date: 2025-12-19 20:01:26.402443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b46f905d53f2'
down_revision: Union[str, Sequence[str], None] = '90475e75a94f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
