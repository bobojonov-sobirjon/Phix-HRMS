"""increase_alembic_version_column_length

Revision ID: 90475e75a94f
Revises: d334f95e8f2a
Create Date: 2025-12-19 19:57:45.208817

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '90475e75a94f'
down_revision: Union[str, Sequence[str], None] = 'd334f95e8f2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Increase alembic_version.version_num column length."""
    # Check if alembic_version table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'alembic_version' not in inspector.get_table_names():
        print("alembic_version table does not exist, skipping migration")
        return
    
    # Get current column info
    columns = {col['name']: col for col in inspector.get_columns('alembic_version')}
    
    if 'version_num' in columns:
        # Alter the column to increase its length to VARCHAR(255)
        # This allows for longer revision identifiers
        op.alter_column(
            'alembic_version',
            'version_num',
            type_=sa.String(255),
            existing_type=sa.String(32),
            existing_nullable=False
        )
        print("Increased alembic_version.version_num column length to 255")
    else:
        print("version_num column does not exist in alembic_version table")


def downgrade() -> None:
    """Revert alembic_version.version_num column length back to original."""
    # Check if alembic_version table exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'alembic_version' not in inspector.get_table_names():
        print("alembic_version table does not exist, skipping downgrade")
        return
    
    # Get current column info
    columns = {col['name']: col for col in inspector.get_columns('alembic_version')}
    
    if 'version_num' in columns:
        # Revert the column back to VARCHAR(32)
        # Note: This might fail if there are version numbers longer than 32 characters
        op.alter_column(
            'alembic_version',
            'version_num',
            type_=sa.String(32),
            existing_type=sa.String(255),
            existing_nullable=False
        )
        print("Reverted alembic_version.version_num column length back to 32")
    else:
        print("version_num column does not exist in alembic_version table")
