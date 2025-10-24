"""create_gig_jobs_table

Revision ID: e17310649136
Revises: 
Create Date: 2025-10-24 16:15:28.003744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e17310649136'
down_revision: Union[str, Sequence[str], None] = '58b59e6b47e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the ExperienceLevel enum if it doesn't exist
    try:
        experience_level_enum = postgresql.ENUM(
            'ENTRY_LEVEL',
            'MID_LEVEL', 
            'JUNIOR',
            'DIRECTOR',
            name='experiencelevel'
        )
        experience_level_enum.create(op.get_bind())
    except Exception:
        # Enum already exists, create reference to existing enum
        experience_level_enum = postgresql.ENUM(
            'ENTRY_LEVEL',
            'MID_LEVEL', 
            'JUNIOR',
            'DIRECTOR',
            name='experiencelevel',
            create_type=False
        )
    
    # Create the GigJobStatus enum if it doesn't exist
    try:
        gig_job_status_enum = postgresql.ENUM(
            'active',
            'in_progress',
            'completed',
            'cancelled',
            name='gigjobstatus'
        )
        gig_job_status_enum.create(op.get_bind())
    except Exception:
        # Enum already exists, create reference to existing enum
        gig_job_status_enum = postgresql.ENUM(
            'active',
            'in_progress',
            'completed',
            'cancelled',
            name='gigjobstatus',
            create_type=False
        )
    
    # Create the ProjectLength enum if it doesn't exist
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
        # Enum already exists, create reference to existing enum
        project_length_enum = postgresql.ENUM(
            'LESS_THAN_ONE_MONTH',
            'ONE_TO_THREE_MONTHS', 
            'THREE_TO_SIX_MONTHS',
            'MORE_THAN_SIX_MONTHS',
            name='projectlength',
            create_type=False
        )
    
    # Check if gig_jobs table already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'gig_jobs' not in tables:
        # Create gig_jobs table
        op.create_table(
            'gig_jobs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('location_id', sa.Integer(), nullable=True),
            sa.Column('experience_level', experience_level_enum, nullable=False),
            sa.Column('project_length', project_length_enum, nullable=False),
            sa.Column('min_salary', sa.Float(), nullable=False),
            sa.Column('max_salary', sa.Float(), nullable=False),
            sa.Column('status', gig_job_status_enum, nullable=True),
            sa.Column('author_id', sa.Integer(), nullable=False),
            sa.Column('category_id', sa.Integer(), nullable=False),
            sa.Column('subcategory_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
            sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
            sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
            sa.ForeignKeyConstraint(['subcategory_id'], ['categories.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_gig_jobs_id', 'gig_jobs', ['id'])
        op.create_index('ix_gig_jobs_title', 'gig_jobs', ['title'])
    
    # Check if gig_job_skills table already exists
    if 'gig_job_skills' not in tables:
        # Create gig_job_skills table
        op.create_table(
            'gig_job_skills',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('gig_job_id', sa.Integer(), nullable=False),
            sa.Column('skill_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.ForeignKeyConstraint(['gig_job_id'], ['gig_jobs.id'], ),
            sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create index for gig_job_skills
        op.create_index('ix_gig_job_skills_id', 'gig_job_skills', ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Check if tables exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    if 'gig_job_skills' in tables:
        op.drop_index('ix_gig_job_skills_id', table_name='gig_job_skills')
        op.drop_table('gig_job_skills')
    
    if 'gig_jobs' in tables:
        op.drop_index('ix_gig_jobs_title', table_name='gig_jobs')
        op.drop_index('ix_gig_jobs_id', table_name='gig_jobs')
        op.drop_table('gig_jobs')
    
    # Drop enums only if they exist and are not used by other tables
    # Note: We should be careful about dropping enums as they might be used by other tables
    # For now, we'll skip dropping enums in downgrade to avoid breaking other tables
