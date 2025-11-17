"""add_is_read_to_proposals

Revision ID: 56e7785b061b
Revises: add_user_device_token_table
Create Date: 2025-11-17 21:47:38.537847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56e7785b061b'
down_revision: Union[str, Sequence[str], None] = 'add_user_device_token_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if proposals table exists
    if 'proposals' not in inspector.get_table_names():
        print("proposals table does not exist, skipping migration")
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('proposals')]
    if 'is_read' in columns:
        print("is_read column already exists, skipping migration")
        return
    
    # Add is_read column to proposals table
    op.add_column('proposals', sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if proposals table exists
    if 'proposals' not in inspector.get_table_names():
        print("proposals table does not exist, skipping downgrade")
        return
    
    # Check if column exists before dropping
    columns = [col['name'] for col in inspector.get_columns('proposals')]
    if 'is_read' not in columns:
        print("is_read column does not exist, skipping downgrade")
        return
    
    # Remove is_read column from proposals table
    op.drop_column('proposals', 'is_read')
