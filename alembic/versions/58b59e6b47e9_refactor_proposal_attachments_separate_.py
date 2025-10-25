"""refactor_proposal_attachments_separate_table

Revision ID: 58b59e6b47e9
Revises: c74fa4791633
Create Date: 2025-10-24 11:20:39.531878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58b59e6b47e9'
down_revision: Union[str, Sequence[str], None] = 'c74fa4791633'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if required tables exist before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if proposals table exists (required for foreign key)
    if 'proposals' not in tables:
        print("proposals table does not exist, skipping migration")
        return
    
    # Check if proposal_attachments table already exists
    if 'proposal_attachments' in tables:
        print("proposal_attachments table already exists, skipping creation")
    else:
        # Create proposal_attachments table
        op.create_table('proposal_attachments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('proposal_id', sa.Integer(), nullable=False),
            sa.Column('attachment', sa.String(), nullable=False),
            sa.Column('size', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_proposal_attachments_id'), 'proposal_attachments', ['id'], unique=False)
    
    # Check if attachments column exists before removing it
    columns = [col['name'] for col in inspector.get_columns('proposals')]
    if 'attachments' in columns:
        # Remove attachments column from proposals table
        op.drop_column('proposals', 'attachments')
    else:
        print("attachments column does not exist in proposals table, skipping removal")


def downgrade() -> None:
    """Downgrade schema."""
    # Check if required tables exist before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()
    
    # Check if proposals table exists
    if 'proposals' not in tables:
        print("proposals table does not exist, skipping downgrade")
        return
    
    # Check if attachments column exists before adding it back
    columns = [col['name'] for col in inspector.get_columns('proposals')]
    if 'attachments' not in columns:
        # Add back attachments column to proposals table
        op.add_column('proposals', sa.Column('attachments', sa.TEXT(), nullable=True))
    else:
        print("attachments column already exists in proposals table, skipping addition")
    
    # Check if proposal_attachments table exists before dropping it
    if 'proposal_attachments' in tables:
        # Drop proposal_attachments table
        op.drop_index(op.f('ix_proposal_attachments_id'), table_name='proposal_attachments')
        op.drop_table('proposal_attachments')
    else:
        print("proposal_attachments table does not exist, skipping drop")
