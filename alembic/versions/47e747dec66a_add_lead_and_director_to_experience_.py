"""add_lead_and_director_to_experience_level_enum

Revision ID: 47e747dec66a
Revises: 24d36116cb81
Create Date: 2025-10-04 19:51:06.863751

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47e747dec66a'
down_revision: Union[str, Sequence[str], None] = '24d36116cb81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if the enum type exists before trying to modify it
    connection = op.get_bind()
    
    # Check if experiencelevel enum type exists
    result = connection.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_type 
            WHERE typname = 'experiencelevel'
        )
    """))
    enum_exists = result.scalar()
    
    if not enum_exists:
        print("experiencelevel enum type does not exist, skipping migration")
        return
    
    # Get existing enum values
    result = connection.execute(sa.text("""
        SELECT e.enumlabel
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'experiencelevel'
    """))
    existing_values = [row[0] for row in result]
    
    # Add 'LEAD' if it doesn't exist
    if 'LEAD' not in existing_values:
        op.execute("ALTER TYPE experiencelevel ADD VALUE 'LEAD'")
    
    # Add 'DIRECTOR' if it doesn't exist
    if 'DIRECTOR' not in existing_values:
        op.execute("ALTER TYPE experiencelevel ADD VALUE 'DIRECTOR'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require dropping and recreating the enum and all dependent columns
    # For safety, we're leaving this as a no-op
    pass
