"""Remove job_type, work_mode, remote_only, deadline_days fields and add project_length field to GigJob model

Revision ID: 9b280e01a71f
Revises: 24d36116cb81
Create Date: 2025-09-21 23:41:56.694298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9b280e01a71f'
down_revision: Union[str, Sequence[str], None] = 'merge_manual_heads'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if columns already exist before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('gig_jobs')]
    
    # Create the new ProjectLength enum if it doesn't exist
    try:
        project_length_enum = postgresql.ENUM(
            'LESS_THAN_ONE_MONTH',
            'ONE_TO_THREE_MONTHS', 
            'THREE_TO_SIX_MONTHS',
            'MORE_THAN_SIX_MONTHS',
            name='projectlength'
        )
        project_length_enum.create(op.get_bind())
    except Exception:
        # Enum already exists, continue
        pass
    
    # Add the new project_length column if it doesn't exist
    if 'project_length' not in columns:
        project_length_enum = postgresql.ENUM(
            'LESS_THAN_ONE_MONTH',
            'ONE_TO_THREE_MONTHS', 
            'THREE_TO_SIX_MONTHS',
            'MORE_THAN_SIX_MONTHS',
            name='projectlength'
        )
        op.add_column('gig_jobs', sa.Column('project_length', project_length_enum, nullable=False, server_default='LESS_THAN_ONE_MONTH'))
    
    # Remove the old columns if they exist
    if 'job_type' in columns:
        op.drop_column('gig_jobs', 'job_type')
    if 'work_mode' in columns:
        op.drop_column('gig_jobs', 'work_mode')
    if 'remote_only' in columns:
        op.drop_column('gig_jobs', 'remote_only')
    if 'deadline_days' in columns:
        op.drop_column('gig_jobs', 'deadline_days')
    
    # Note: Not dropping jobtype and workmode enums as they are still used by full_time_jobs table


def downgrade() -> None:
    """Downgrade schema."""
    # Check if columns already exist before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('gig_jobs')]
    
    # Note: jobtype and workmode enums still exist as they are used by full_time_jobs table
    
    # Add back the old columns if they don't exist
    if 'job_type' not in columns:
        op.add_column('gig_jobs', sa.Column('job_type', postgresql.ENUM('FULL_TIME', 'PART_TIME', 'FREELANCE', 'INTERNSHIP', name='jobtype'), nullable=False, server_default='FREELANCE'))
    if 'work_mode' not in columns:
        op.add_column('gig_jobs', sa.Column('work_mode', postgresql.ENUM('ON_SITE', 'REMOTE', 'HYBRID', 'FLEXIBLE_HOURS', name='workmode'), nullable=False, server_default='REMOTE'))
    if 'remote_only' not in columns:
        op.add_column('gig_jobs', sa.Column('remote_only', sa.Boolean(), nullable=True, server_default='false'))
    if 'deadline_days' not in columns:
        op.add_column('gig_jobs', sa.Column('deadline_days', sa.Integer(), nullable=False, server_default='7'))
    
    # Remove the new column if it exists
    if 'project_length' in columns:
        op.drop_column('gig_jobs', 'project_length')
    
    # Drop the new enum
    op.execute('DROP TYPE IF EXISTS projectlength')
