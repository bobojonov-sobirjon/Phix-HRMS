"""Add chat tables for real-time messaging

Revision ID: chat_tables_manual
Revises: 9b280e01a71f
Create Date: 2024-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'chat_tables_manual'
down_revision = '352229f0c93a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add chat tables for real-time messaging."""
    
    # Create MessageType enum if it doesn't exist
    op.execute("DO $$ BEGIN CREATE TYPE messagetype AS ENUM ('text', 'image', 'file'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Define the enum for use in table creation
    message_type_enum = postgresql.ENUM('text', 'image', 'file', name='messagetype')
    
    # Create chat_rooms table
    op.create_table('chat_rooms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('room_type', sa.String(length=50), nullable=False, server_default='direct'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_rooms_id'), 'chat_rooms', ['id'], unique=False)
    
    # Create chat_participants table
    op.create_table('chat_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_participants_id'), 'chat_participants', ['id'], unique=False)
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('message_type', message_type_enum, nullable=False, server_default='text'),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['receiver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    
    # Create user_presence table
    op.create_table('user_presence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_online', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_presence_id'), 'user_presence', ['id'], unique=False)


def downgrade() -> None:
    """Remove chat tables."""
    
    # Drop tables
    op.drop_table('user_presence')
    op.drop_table('chat_messages')
    op.drop_table('chat_participants')
    op.drop_table('chat_rooms')
    
    # Drop MessageType enum
    message_type_enum = postgresql.ENUM('text', 'image', 'file', name='messagetype')
    message_type_enum.drop(op.get_bind())
