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
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if chat_rooms table exists
    if 'chat_rooms' not in inspector.get_table_names():
        print("chat_rooms table does not exist, skipping migration")
        return
    
    # Check if updated_at column exists
    columns = [col['name'] for col in inspector.get_columns('chat_rooms')]
    if 'updated_at' not in columns:
        print("updated_at column does not exist in chat_rooms, skipping migration")
        return
    
    # Add server_default to updated_at column
    op.alter_column('chat_rooms', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    server_default=sa.text('now()'),
                    existing_nullable=True)


def downgrade() -> None:
    """Remove server_default from updated_at column in chat_rooms table"""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if chat_rooms table exists
    if 'chat_rooms' not in inspector.get_table_names():
        print("chat_rooms table does not exist, skipping downgrade")
        return
    
    # Check if updated_at column exists
    columns = [col['name'] for col in inspector.get_columns('chat_rooms')]
    if 'updated_at' not in columns:
        print("updated_at column does not exist in chat_rooms, skipping downgrade")
        return
    
    # Remove server_default from updated_at column
    op.alter_column('chat_rooms', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(timezone=True),
                    server_default=None,
                    existing_nullable=True)
