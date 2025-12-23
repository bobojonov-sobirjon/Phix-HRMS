"""add_agora_tokens_table

Revision ID: 63591ea2c286
Revises: b6ad4cbff0fa
Create Date: 2025-12-24 00:26:11.418654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63591ea2c286'
down_revision: Union[str, Sequence[str], None] = 'b6ad4cbff0fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create agora_tokens table
    op.create_table(
        'agora_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('room_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('channel_name', sa.String(length=255), nullable=False),
        sa.Column('uid', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='publisher'),
        sa.Column('expire_seconds', sa.Integer(), nullable=False, server_default='3600'),
        sa.Column('expire_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['room_id'], ['chat_rooms.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id')
    )
    op.create_index('ix_agora_tokens_id', 'agora_tokens', ['id'], unique=False)
    op.create_index('ix_agora_tokens_room_id', 'agora_tokens', ['room_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop agora_tokens table
    op.drop_index('ix_agora_tokens_room_id', table_name='agora_tokens')
    op.drop_index('ix_agora_tokens_id', table_name='agora_tokens')
    op.drop_table('agora_tokens')
