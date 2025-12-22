"""add_blocking_fields_to_users

Revision ID: db4a2439573a
Revises: b46f905d53f2
Create Date: 2025-12-22 11:24:45.546624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db4a2439573a'
down_revision: Union[str, Sequence[str], None] = 'b46f905d53f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
        print("users table does not exist, skipping migration")
        return
    
    # Check if columns already exist
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add blocked_at column if it doesn't exist
    if 'blocked_at' not in columns:
        op.add_column('users', sa.Column('blocked_at', sa.DateTime(timezone=True), nullable=True))
    
    # Add block_reason column if it doesn't exist
    if 'block_reason' not in columns:
        op.add_column('users', sa.Column('block_reason', sa.Text(), nullable=True))
    
    # Add blocked_by column if it doesn't exist
    if 'blocked_by' not in columns:
        op.add_column('users', sa.Column('blocked_by', sa.Integer(), nullable=True))
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_users_blocked_by',
            'users', 'users',
            ['blocked_by'], ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
        print("users table does not exist, skipping downgrade")
        return
    
    # Check if columns exist before dropping
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Drop foreign key constraint if it exists
    try:
        op.drop_constraint('fk_users_blocked_by', 'users', type_='foreignkey')
    except Exception:
        pass
    
    # Remove blocked_by column if it exists
    if 'blocked_by' in columns:
        op.drop_column('users', 'blocked_by')
    
    # Remove block_reason column if it exists
    if 'block_reason' in columns:
        op.drop_column('users', 'block_reason')
    
    # Remove blocked_at column if it exists
    if 'blocked_at' in columns:
        op.drop_column('users', 'blocked_at')
