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
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns to full_time_jobs table
    op.add_column('full_time_jobs', sa.Column('created_by_user_id', sa.Integer(), nullable=False))
    op.add_column('full_time_jobs', sa.Column('created_by_role', sa.Enum('OWNER', 'ADMIN', 'HR_MANAGER', 'RECRUITER', 'VIEWER', name='teammemberrole'), nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key('fk_full_time_jobs_created_by_user_id', 'full_time_jobs', 'users', ['created_by_user_id'], ['id'])
    
    # Add index for better performance
    op.create_index('ix_full_time_jobs_created_by_user_id', 'full_time_jobs', ['created_by_user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove index
    op.drop_index('ix_full_time_jobs_created_by_user_id', table_name='full_time_jobs')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_full_time_jobs_created_by_user_id', 'full_time_jobs', type_='foreignkey')
    
    # Remove columns
    op.drop_column('full_time_jobs', 'created_by_role')
    op.drop_column('full_time_jobs', 'created_by_user_id')

