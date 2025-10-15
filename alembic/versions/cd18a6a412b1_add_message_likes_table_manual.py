"""add_message_likes_table_manual

Revision ID: cd18a6a412b1
Revises: 566a242ef570
Create Date: 2025-10-13 11:36:13.355198

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd18a6a412b1'
down_revision: Union[str, Sequence[str], None] = '566a242ef570'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create message_likes table
    op.create_table('message_likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'user_id', name='unique_message_user_like')
    )
    op.create_index(op.f('ix_message_likes_id'), 'message_likes', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_message_likes_id'), table_name='message_likes')
    op.drop_table('message_likes')
