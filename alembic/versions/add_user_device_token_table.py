"""add_user_device_token_table

Revision ID: add_user_device_token_table
Revises: 444e1bd04f63
Create Date: 2025-11-12 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_user_device_token_table'
down_revision: Union[str, Sequence[str], None] = '444e1bd04f63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_device_tokens table for device token management."""
    # Check if required tables exist before creating user_device_tokens table
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if users table exists (required for foreign key)
    if 'users' not in tables:
        print("users table does not exist, skipping user_device_tokens table creation")
        return
    
    # Check if user_device_tokens table already exists
    if 'user_device_tokens' in tables:
        print("user_device_tokens table already exists, skipping creation")
        return
    
    # Create DeviceType enum if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN 
            CREATE TYPE devicetype AS ENUM ('ios', 'android'); 
        EXCEPTION 
            WHEN duplicate_object THEN null; 
        END $$;
    """)
    
    # Define the enum for use in table creation
    device_type_enum = postgresql.ENUM('ios', 'android', name='devicetype')
    
    # Create user_device_tokens table
    op.create_table(
        'user_device_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_token', sa.Text(), nullable=False),
        sa.Column('device_type', device_type_enum, nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on id column
    op.create_index(op.f('ix_user_device_tokens_id'), 'user_device_tokens', ['id'], unique=False)


def downgrade() -> None:
    """Remove user_device_tokens table."""
    # Check if user_device_tokens table exists before trying to drop it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'user_device_tokens' not in tables:
        print("user_device_tokens table does not exist, skipping downgrade")
        return
    
    op.drop_index('ix_user_device_tokens_id', table_name='user_device_tokens')
    op.drop_table('user_device_tokens')
    
    # Drop enum type (be careful - only if no other tables use it)
    op.execute("DROP TYPE IF EXISTS devicetype")

