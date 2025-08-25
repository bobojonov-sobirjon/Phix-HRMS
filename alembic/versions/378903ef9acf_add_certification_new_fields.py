"""add_certification_new_fields

Revision ID: 378903ef9acf
Revises: 2a8e5ec6b23b
Create Date: 2025-08-23 22:40:35.713169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '378903ef9acf'
down_revision = '2a8e5ec6b23b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to certifications table
    op.add_column('certifications', sa.Column('publishing_organization', sa.String(length=255), nullable=True))
    op.add_column('certifications', sa.Column('certification_url', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('certifications', 'publishing_organization')
    op.drop_column('certifications', 'certification_url') 