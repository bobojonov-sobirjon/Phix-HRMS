"""fix chat rooms updated_at default

Revision ID: fix_chat_rooms_updated_at
Revises: add_pay_period_manual
Create Date: 2025-10-15 09:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fix_chat_rooms_updated_at'
down_revision: Union[str, Sequence[str], None] = 'add_pay_period_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add server_default to updated_at column in chat_rooms table"""
    # Add server_default to updated_at column
    op.alter_column('chat_rooms', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    server_default=sa.text('now()'),
                    existing_nullable=True)


def downgrade() -> None:
    """Remove server_default from updated_at column in chat_rooms table"""
    # Remove server_default from updated_at column
    op.alter_column('chat_rooms', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    server_default=None,
                    existing_nullable=True)
