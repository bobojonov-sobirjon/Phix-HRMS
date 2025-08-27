"""add team member table

Revision ID: 3abc12345678
Revises: 2ea247c60da0
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3abc12345678'
down_revision = '2ea247c60da0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('corporate_profile_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('invited_by_user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),  # Use String instead of ENUM
        sa.Column('status', sa.String(20), nullable=False),  # Use String instead of ENUM
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['corporate_profile_id'], ['corporate_profiles.id'], ),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_members_id'), 'team_members', ['id'], unique=False)


def downgrade() -> None:
    # Drop team_members table
    op.drop_index(op.f('ix_team_members_id'), table_name='team_members')
    op.drop_table('team_members')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS teammemberstatus')
    op.execute('DROP TYPE IF EXISTS teammemberrole')
