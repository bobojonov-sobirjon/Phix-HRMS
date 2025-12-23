"""add_company_name_remove_company_id_from_corporate_profiles

Revision ID: b54df9e3739c
Revises: db4a2439573a
Create Date: 2025-12-23 22:00:27.197626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b54df9e3739c'
down_revision: Union[str, Sequence[str], None] = 'db4a2439573a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    from sqlalchemy import text
    
    connection = op.get_bind()
    
    # First, find and drop the foreign key constraint for company_id
    # PostgreSQL requires us to drop the constraint before dropping the column
    try:
        # Query to find the constraint name
        result = connection.execute(text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'corporate_profiles' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%company_id%'
        """))
        
        constraint_row = result.fetchone()
        if constraint_row:
            constraint_name = constraint_row[0]
            op.drop_constraint(constraint_name, 'corporate_profiles', type_='foreignkey')
    except Exception as e:
        # If we can't find or drop the constraint, try common names
        for constraint_name in ['corporate_profiles_company_id_fkey', 'fk_corporate_profiles_company_id']:
            try:
                op.drop_constraint(constraint_name, 'corporate_profiles', type_='foreignkey')
                break
            except:
                continue
    
    # Add company_name column (with temporary server default for existing rows)
    op.add_column('corporate_profiles', 
                  sa.Column('company_name', sa.String(length=255), nullable=False, server_default='Company'))
    
    # Drop company_id column (now that constraint is removed)
    op.drop_column('corporate_profiles', 'company_id')
    
    # Remove server default after column is created
    op.alter_column('corporate_profiles', 'company_name', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Add company_id column back
    op.add_column('corporate_profiles',
                  sa.Column('company_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint back
    op.create_foreign_key(
        'corporate_profiles_company_id_fkey',
        'corporate_profiles', 'companies',
        ['company_id'], ['id']
    )
    
    # Drop company_name column
    op.drop_column('corporate_profiles', 'company_name')
