"""add_chat_fields_to_notifications

Revision ID: b7294e7b7b78
Revises: 5299035323c9
Create Date: 2025-11-26 17:44:05.707774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7294e7b7b78'
down_revision: Union[str, Sequence[str], None] = '5299035323c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add chat fields to notifications table and CHAT_MESSAGE to enum."""
    # Add CHAT_MESSAGE to NotificationType enum
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'CHAT_MESSAGE'")
    
    # Add chat-related columns to notifications table
    op.add_column('notifications', sa.Column('room_id', sa.Integer(), nullable=True))
    op.add_column('notifications', sa.Column('message_id', sa.Integer(), nullable=True))
    op.add_column('notifications', sa.Column('sender_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_notifications_room_id',
        'notifications', 'chat_rooms',
        ['room_id'], ['id']
    )
    op.create_foreign_key(
        'fk_notifications_message_id',
        'notifications', 'chat_messages',
        ['message_id'], ['id']
    )
    op.create_foreign_key(
        'fk_notifications_sender_id',
        'notifications', 'users',
        ['sender_id'], ['id']
    )
    
    # Create indexes for better query performance
    op.create_index('ix_notifications_room_id', 'notifications', ['room_id'], unique=False)
    op.create_index('ix_notifications_message_id', 'notifications', ['message_id'], unique=False)
    op.create_index('ix_notifications_sender_id', 'notifications', ['sender_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema - Remove chat fields from notifications table."""
    # Drop indexes
    op.drop_index('ix_notifications_sender_id', table_name='notifications')
    op.drop_index('ix_notifications_message_id', table_name='notifications')
    op.drop_index('ix_notifications_room_id', table_name='notifications')
    
    # Drop foreign key constraints
    op.drop_constraint('fk_notifications_sender_id', 'notifications', type_='foreignkey')
    op.drop_constraint('fk_notifications_message_id', 'notifications', type_='foreignkey')
    op.drop_constraint('fk_notifications_room_id', 'notifications', type_='foreignkey')
    
    # Drop columns
    op.drop_column('notifications', 'sender_id')
    op.drop_column('notifications', 'message_id')
    op.drop_column('notifications', 'room_id')
    
    # Note: We cannot remove enum values in PostgreSQL, so CHAT_MESSAGE will remain in the enum
    # This is a limitation of PostgreSQL enums
