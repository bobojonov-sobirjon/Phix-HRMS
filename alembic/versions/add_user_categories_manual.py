"""Add user categories

Revision ID: add_user_categories_manual
Revises: 53fbf96e2640
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_categories_manual'
down_revision = 'add_is_deleted_manual'
branch_labels = None
depends_on = None


def upgrade():
    # Add main_category_id column to users table
    op.add_column('users', sa.Column('main_category_id', sa.Integer(), nullable=True))
    
    # Add sub_category_id column to users table
    op.add_column('users', sa.Column('sub_category_id', sa.Integer(), nullable=True))
    
    # Create foreign key constraints
    op.create_foreign_key('fk_users_main_category', 'users', 'categories', ['main_category_id'], ['id'])
    op.create_foreign_key('fk_users_sub_category', 'users', 'categories', ['sub_category_id'], ['id'])


def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_users_sub_category', 'users', type_='foreignkey')
    op.drop_constraint('fk_users_main_category', 'users', type_='foreignkey')
    
    # Drop columns
    op.drop_column('users', 'sub_category_id')
    op.drop_column('users', 'main_category_id')
