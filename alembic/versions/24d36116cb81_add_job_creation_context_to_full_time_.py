"""Add job creation context to full_time_jobs

Revision ID: 24d36116cb81
Revises: 
Create Date: 2025-09-15 12:47:53.163543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '24d36116cb81'
down_revision: Union[str, Sequence[str], None] = '9b280e01a71f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns already exist before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('full_time_jobs')]
    
    # Add new columns to full_time_jobs table if they don't exist
    if 'created_by_user_id' not in columns:
        op.add_column('full_time_jobs', sa.Column('created_by_user_id', sa.Integer(), nullable=False))
    
    if 'created_by_role' not in columns:
        op.add_column('full_time_jobs', sa.Column('created_by_role', sa.Enum('OWNER', 'ADMIN', 'HR_MANAGER', 'RECRUITER', 'VIEWER', name='teammemberrole'), nullable=False))
    
    # Add foreign key constraint if it doesn't exist
    try:
        op.create_foreign_key('fk_full_time_jobs_created_by_user_id', 'full_time_jobs', 'users', ['created_by_user_id'], ['id'])
    except Exception:
        # Foreign key already exists, continue
        pass
    
    # Add index for better performance if it doesn't exist
    try:
        op.create_index('ix_full_time_jobs_created_by_user_id', 'full_time_jobs', ['created_by_user_id'])
    except Exception:
        # Index already exists, continue
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # Check if columns exist before trying to remove them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('full_time_jobs')]
    
    # Remove index if it exists
    try:
        op.drop_index('ix_full_time_jobs_created_by_user_id', table_name='full_time_jobs')
    except Exception:
        # Index doesn't exist, continue
        pass
    
    # Remove foreign key constraint if it exists
    try:
        op.drop_constraint('fk_full_time_jobs_created_by_user_id', 'full_time_jobs', type_='foreignkey')
    except Exception:
        # Foreign key doesn't exist, continue
        pass
    
    # Remove columns if they exist
    if 'created_by_role' in columns:
        op.drop_column('full_time_jobs', 'created_by_role')
    if 'created_by_user_id' in columns:
        op.drop_column('full_time_jobs', 'created_by_user_id')

