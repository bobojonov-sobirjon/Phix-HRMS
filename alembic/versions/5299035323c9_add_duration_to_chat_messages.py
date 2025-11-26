"""add_duration_to_chat_messages

Revision ID: 5299035323c9
Revises: 98a085243041
Create Date: 2025-11-26 15:34:53.199772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5299035323c9'
down_revision: Union[str, Sequence[str], None] = '98a085243041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if chat_messages table exists
    if 'chat_messages' not in inspector.get_table_names():
        print("chat_messages table does not exist, skipping migration")
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    if 'duration' not in columns:
        # Add duration column to chat_messages table
        op.add_column('chat_messages', sa.Column('duration', sa.Integer(), nullable=True))
        print("duration column added to chat_messages table")
    else:
        print("duration column already exists, skipping migration")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if chat_messages table exists
    if 'chat_messages' not in inspector.get_table_names():
        print("chat_messages table does not exist, skipping downgrade")
        return
    
    # Check if column exists before trying to remove it
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]
    if 'duration' in columns:
        # Remove duration column from chat_messages table
        op.drop_column('chat_messages', 'duration')
        print("duration column removed from chat_messages table")
    else:
        print("duration column does not exist, skipping downgrade")
