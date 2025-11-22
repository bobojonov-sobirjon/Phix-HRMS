"""add_notifications_table

Revision ID: 98a085243041
Revises: 56e7785b061b
Create Date: 2025-11-22 23:01:09.618738

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '98a085243041'
down_revision: Union[str, Sequence[str], None] = '56e7785b061b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add notifications table."""
    # Create notification type enum
    notification_type_enum = postgresql.ENUM('APPLICATION', 'PROPOSAL_VIEWED', name='notificationtype', create_type=False)
    notification_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create notifications table
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', notification_type_enum, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('recipient_user_id', sa.Integer(), nullable=False),
    sa.Column('proposal_id', sa.Integer(), nullable=True),
    sa.Column('job_id', sa.Integer(), nullable=True),
    sa.Column('job_type', sa.String(length=20), nullable=True),
    sa.Column('applicant_id', sa.Integer(), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['proposal_id'], ['proposals.id'], ),
    sa.ForeignKeyConstraint(['recipient_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)
    op.create_index(op.f('ix_notifications_recipient_user_id'), 'notifications', ['recipient_user_id'], unique=False)
    op.create_index(op.f('ix_notifications_type'), 'notifications', ['type'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove notifications table."""
    # Drop indexes
    op.drop_index(op.f('ix_notifications_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_recipient_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_is_read'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS notificationtype")
