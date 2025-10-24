"""add_files_data_to_chat_messages

Revision ID: 566a242ef570
Revises: 47e747dec66a
Create Date: 2025-10-13 09:59:44.634347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '566a242ef570'
down_revision: Union[str, Sequence[str], None] = '47e747dec66a'
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
    if 'files_data' not in columns:
        # Add files_data column to chat_messages table
        op.add_column('chat_messages', sa.Column('files_data', sa.JSON(), nullable=True))
    else:
        print("files_data column already exists, skipping migration")


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
    if 'files_data' in columns:
        # Remove files_data column from chat_messages table
        op.drop_column('chat_messages', 'files_data')
    else:
        print("files_data column does not exist, skipping downgrade")
