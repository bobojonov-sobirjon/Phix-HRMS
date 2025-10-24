"""add_saved_jobs_table_manual

Revision ID: add_saved_jobs_manual
Revises: 352229f0c93a
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_saved_jobs_manual'
down_revision: Union[str, Sequence[str], None] = '352229f0c93a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if required tables exist before creating saved_jobs table
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if users table exists (required for foreign key)
    if 'users' not in tables:
        print("users table does not exist, skipping saved_jobs table creation")
        return
    
    # Check if gig_jobs table exists (required for foreign key)
    if 'gig_jobs' not in tables:
        print("gig_jobs table does not exist, skipping saved_jobs table creation")
        return
    
    # Check if full_time_jobs table exists (required for foreign key)
    if 'full_time_jobs' not in tables:
        print("full_time_jobs table does not exist, skipping saved_jobs table creation")
        return
    
    # Check if saved_jobs table already exists
    if 'saved_jobs' in tables:
        print("saved_jobs table already exists, skipping creation")
        return
    
    # Create saved_jobs table
    op.create_table(
        'saved_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gig_job_id', sa.Integer(), nullable=True),
        sa.Column('full_time_job_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['full_time_job_id'], ['full_time_jobs.id']),
        sa.ForeignKeyConstraint(['gig_job_id'], ['gig_jobs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on id column
    op.create_index('ix_saved_jobs_id', 'saved_jobs', ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Check if saved_jobs table exists before trying to drop it
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'saved_jobs' not in tables:
        print("saved_jobs table does not exist, skipping downgrade")
        return
    
    op.drop_index('ix_saved_jobs_id', table_name='saved_jobs')
    op.drop_table('saved_jobs')

