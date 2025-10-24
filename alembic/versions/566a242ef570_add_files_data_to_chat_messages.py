"""add_files_data_to_chat_messages

Revision ID: 566a242ef570
Revises: 47e747dec66a
Create Date: 2025-10-13 09:59:44.634347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '566a242ef570'
down_revision: Union[str, Sequence[str], None] = 'cd18a6a412b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add files_data column to chat_messages table
    op.add_column('chat_messages', sa.Column('files_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove files_data column from chat_messages table
    op.drop_column('chat_messages', 'files_data')
