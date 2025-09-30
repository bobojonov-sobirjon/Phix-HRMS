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
    # Create saved_jobs table
    op.create_table('saved_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gig_job_id', sa.Integer(), nullable=True),
        sa.Column('full_time_job_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['full_time_job_id'], ['full_time_jobs.id'], ),
        sa.ForeignKeyConstraint(['gig_job_id'], ['gig_jobs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_saved_jobs_id'), 'saved_jobs', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_saved_jobs_id'), table_name='saved_jobs')
    op.drop_table('saved_jobs')
