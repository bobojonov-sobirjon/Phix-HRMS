"""Replace agora_tokens with agora_channels - only store channel name

Revision ID: 2dcd2083375d
Revises: 63591ea2c286
Create Date: 2026-01-18 22:44:50.997345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2dcd2083375d'
down_revision: Union[str, Sequence[str], None] = '63591ea2c286'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Replace agora_tokens with agora_channels."""
    # Create new agora_channels table
    op.create_table('agora_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('channel_name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel_name'),
        sa.UniqueConstraint('room_id')
    )
    op.create_index(op.f('ix_agora_channels_id'), 'agora_channels', ['id'], unique=False)
    
    # Drop old agora_tokens table
    op.drop_index(op.f('ix_agora_tokens_room_id'), table_name='agora_tokens')
    op.drop_index(op.f('ix_agora_tokens_id'), table_name='agora_tokens')
    op.drop_table('agora_tokens')


def downgrade() -> None:
    """Downgrade schema: Restore agora_tokens from agora_channels."""
    # Recreate agora_tokens table
    op.create_table('agora_tokens',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('token', sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column('channel_name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column('uid', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('role', sa.VARCHAR(length=50), server_default=sa.text("'publisher'::character varying"), autoincrement=False, nullable=False),
        sa.Column('expire_seconds', sa.INTEGER(), server_default=sa.text('3600'), autoincrement=False, nullable=False),
        sa.Column('expire_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], name=op.f('agora_tokens_room_id_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('agora_tokens_pkey')),
        sa.UniqueConstraint('room_id', name=op.f('agora_tokens_room_id_key'))
    )
    op.create_index(op.f('ix_agora_tokens_room_id'), 'agora_tokens', ['room_id'], unique=True)
    op.create_index(op.f('ix_agora_tokens_id'), 'agora_tokens', ['id'], unique=False)
    
    # Drop agora_channels table
    op.drop_index(op.f('ix_agora_channels_id'), table_name='agora_channels')
    op.drop_table('agora_channels')
