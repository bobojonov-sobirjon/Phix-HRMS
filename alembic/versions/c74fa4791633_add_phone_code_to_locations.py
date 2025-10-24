"""add phone_code to locations

Revision ID: c74fa4791633
Revises: fix_chat_rooms_updated_at
Create Date: 2025-10-24 10:54:49.996593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c74fa4791633'
down_revision: Union[str, Sequence[str], None] = 'fix_chat_rooms_updated_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if locations table exists
    if 'locations' not in inspector.get_table_names():
        print("locations table does not exist, skipping migration")
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('locations')]
    if 'phone_code' in columns:
        print("phone_code column already exists, skipping migration")
        return
    
    # Add phone_code column to locations table
    op.add_column('locations', sa.Column('phone_code', sa.String(length=10), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if locations table exists
    if 'locations' not in inspector.get_table_names():
        print("locations table does not exist, skipping downgrade")
        return
    
    # Check if column exists before dropping
    columns = [col['name'] for col in inspector.get_columns('locations')]
    if 'phone_code' not in columns:
        print("phone_code column does not exist, skipping downgrade")
        return
    
    # Drop phone_code column from locations table
    op.drop_column('locations', 'phone_code')
