"""add_voice_to_message_type_enum

Revision ID: 352229f0c93a
Revises: 53fbf96e2640
Create Date: 2025-09-22 22:29:51.355817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '352229f0c93a'
down_revision: Union[str, Sequence[str], None] = 'cd18a6a412b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if the messagetype enum exists before trying to modify it
    connection = op.get_bind()
    
    # Check if messagetype enum exists
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type 
            WHERE typname = 'messagetype'
        )
    """))
    enum_exists = result.scalar()
    
    if not enum_exists:
        print("messagetype enum does not exist, skipping migration")
        return
    
    # Add 'voice' and 'VOICE' to the messagetype enum if they don't exist
    try:
        op.execute("ALTER TYPE messagetype ADD VALUE 'voice'")
    except Exception:
        # Value already exists, continue
        pass
    
    try:
        op.execute("ALTER TYPE messagetype ADD VALUE 'VOICE'")
    except Exception:
        # Value already exists, continue
        pass


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and updating all references
    # For now, we'll leave the voice value in the enum
    pass
