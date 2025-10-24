"""add_is_deleted_to_corporate_profiles_manual

Revision ID: add_is_deleted_manual
Revises: add_saved_jobs_manual
Create Date: 2025-09-30 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_is_deleted_manual'
down_revision: Union[str, Sequence[str], None] = 'add_saved_jobs_manual'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_deleted column to corporate_profiles table."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if corporate_profiles table exists
    if 'corporate_profiles' not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping migration")
        return
    
    # Check if column already exists before adding
    columns = [col['name'] for col in inspector.get_columns('corporate_profiles')]
    
    if 'is_deleted' not in columns:
        op.add_column('corporate_profiles', sa.Column('is_deleted', sa.Boolean(), nullable=True, default=False))
        
        # Set all existing records to is_deleted = False
        op.execute("UPDATE corporate_profiles SET is_deleted = false WHERE is_deleted IS NULL")
    else:
        print("is_deleted column already exists, skipping migration")


def downgrade() -> None:
    """Remove is_deleted column from corporate_profiles table."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if corporate_profiles table exists
    if 'corporate_profiles' not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping downgrade")
        return
    
    # Check if column exists before trying to remove it
    columns = [col['name'] for col in inspector.get_columns('corporate_profiles')]
    if 'is_deleted' in columns:
        op.drop_column('corporate_profiles', 'is_deleted')
    else:
        print("is_deleted column does not exist, skipping downgrade")
