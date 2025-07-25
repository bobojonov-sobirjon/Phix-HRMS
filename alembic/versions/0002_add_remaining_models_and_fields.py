"""
Add remaining models and update user fields

Revision ID: 0002
Revises: 0001
Create Date: 2024-10-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add missing columns to users (without FK yet)
    op.add_column('users', sa.Column('about_me', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('current_position', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('location_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), nullable=True))

    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('flag_image', sa.Text(), nullable=True),
        sa.Column('code', sa.String(length=10), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_locations_id'), 'locations', ['id'], unique=False)

    # Now add foreign key to users after locations exists
    op.create_foreign_key(None, 'users', 'locations', ['location_id'], ['id'])

    # Create certifications table
    op.create_table('certifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('publishing_organization', sa.String(length=255), nullable=False),
        sa.Column('from_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('to_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('certificate_id', sa.String(length=255), nullable=True),
        sa.Column('certificate_path', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_certifications_id'), 'certifications', ['id'], unique=False)

    # Create educations table
    op.create_table('educations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('degree', sa.String(length=255), nullable=False),
        sa.Column('school', sa.String(length=255), nullable=False),
        sa.Column('from_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('to_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_graduate', sa.Boolean(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_educations_id'), 'educations', ['id'], unique=False)

    # Create experiences table
    op.create_table('experiences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('from_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('to_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=True),
        sa.Column('industry', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('job_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiences_id'), 'experiences', ['id'], unique=False)

    # Create skills table
    op.create_table('skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_id'), 'skills', ['id'], unique=False)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('from_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('to_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('live_project_path', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # Create user_skills table
    op.create_table('user_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_skills_id'), 'user_skills', ['id'], unique=False)

    # Create project_images table
    op.create_table('project_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('image', sa.Text(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_images_id'), 'project_images', ['id'], unique=False)

def downgrade() -> None:
    # Drop project_images
    op.drop_index('ix_project_images_id', table_name='project_images')
    op.drop_table('project_images')
    # Drop user_skills
    op.drop_index('ix_user_skills_id', table_name='user_skills')
    op.drop_table('user_skills')
    # Drop projects
    op.drop_index('ix_projects_id', table_name='projects')
    op.drop_table('projects')
    # Drop skills
    op.drop_index('ix_skills_id', table_name='skills')
    op.drop_table('skills')
    # Drop experiences
    op.drop_index('ix_experiences_id', table_name='experiences')
    op.drop_table('experiences')
    # Drop educations
    op.drop_index('ix_educations_id', table_name='educations')
    op.drop_table('educations')
    # Drop certifications
    op.drop_index('ix_certifications_id', table_name='certifications')
    op.drop_table('certifications')
    # Drop foreign key from users
    op.drop_constraint(None, 'users', type_='foreignkey')
    # Drop locations
    op.drop_index('ix_locations_id', table_name='locations')
    op.drop_table('locations')
    # Remove added columns from users
    op.drop_column('users', 'is_deleted')
    op.drop_column('users', 'location_id')
    op.drop_column('users', 'current_position')
    op.drop_column('users', 'about_me') 