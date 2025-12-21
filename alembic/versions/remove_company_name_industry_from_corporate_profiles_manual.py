"""remove_company_name_industry_from_corporate_profiles_manual

Revision ID: remove_company_name_industry_manual
Revises: add_company_and_category_manual
Create Date: 2025-01-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_company_name_industry_manual'
down_revision: Union[str, Sequence[str], None] = 'add_comp_cat_corp'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove company_name and industry columns from corporate_profiles table."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if corporate_profiles table exists
    if 'corporate_profiles' not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping migration")
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('corporate_profiles')]
    
    # Remove company_name column if it exists
    if 'company_name' in columns:
        # Drop index if exists
        indexes = [idx['name'] for idx in inspector.get_indexes('corporate_profiles')]
        if 'ix_corporate_profiles_company_name' in indexes:
            op.drop_index('ix_corporate_profiles_company_name', table_name='corporate_profiles')
        op.drop_column('corporate_profiles', 'company_name')
        print("Removed company_name column from corporate_profiles")
    else:
        print("company_name column does not exist, skipping")
    
    # Remove industry column if it exists
    if 'industry' in columns:
        op.drop_column('corporate_profiles', 'industry')
        print("Removed industry column from corporate_profiles")
    else:
        print("industry column does not exist, skipping")


def downgrade() -> None:
    """Add back company_name and industry columns to corporate_profiles table."""
    # Check if table exists before making changes
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Check if corporate_profiles table exists
    if 'corporate_profiles' not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping downgrade")
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('corporate_profiles')]
    
    # Add industry column if it doesn't exist
    if 'industry' not in columns:
        op.add_column('corporate_profiles', sa.Column('industry', sa.String(100), nullable=True))
        # Update existing rows: set industry from company.name if company_id exists
        op.execute("""
            UPDATE corporate_profiles cp
            SET industry = c.name
            FROM companies c
            WHERE cp.company_id = c.id AND cp.industry IS NULL
        """)
        # Make it nullable=False after updating
        op.alter_column('corporate_profiles', 'industry', nullable=False)
        print("Added industry column back to corporate_profiles")
    else:
        print("industry column already exists, skipping")
    
    # Add company_name column if it doesn't exist
    if 'company_name' not in columns:
        op.add_column('corporate_profiles', sa.Column('company_name', sa.String(255), nullable=True))
        # Update existing rows: set company_name from company.name if company_id exists
        op.execute("""
            UPDATE corporate_profiles cp
            SET company_name = c.name
            FROM companies c
            WHERE cp.company_id = c.id AND cp.company_name IS NULL
        """)
        # Make it nullable=False after updating
        op.alter_column('corporate_profiles', 'company_name', nullable=False)
        # Create index
        op.create_index('ix_corporate_profiles_company_name', 'corporate_profiles', ['company_name'])
        print("Added company_name column back to corporate_profiles")
    else:
        print("company_name column already exists, skipping")

