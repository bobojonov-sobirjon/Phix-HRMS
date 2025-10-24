"""merge_heads

Revision ID: 2acd05c72b2f
Revises: 53fbf96e2640, 58b59e6b47e9, chat_tables_manual
Create Date: 2025-10-24 16:30:40.004911

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2acd05c72b2f'
down_revision: Union[str, Sequence[str], None] = ('53fbf96e2640', '58b59e6b47e9', 'chat_tables_manual')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
