"""add_company_and_category_to_corporate_profiles_manual

Revision ID: add_company_category_to_corporate_profiles
Revises: add_is_deleted_manual
Create Date: 2025-12-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "add_comp_cat_corp"
down_revision: Union[str, Sequence[str], None] = "add_is_deleted_manual"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add company_id and category_id columns to corporate_profiles table."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Ensure table exists
    if "corporate_profiles" not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping migration")
        return

    columns = [col["name"] for col in inspector.get_columns("corporate_profiles")]

    if "company_id" not in columns:
        op.add_column(
            "corporate_profiles",
            sa.Column("company_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_corporate_profiles_company_id_companies",
            "corporate_profiles",
            "companies",
            ["company_id"],
            ["id"],
        )

    if "category_id" not in columns:
        op.add_column(
            "corporate_profiles",
            sa.Column("category_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            "fk_corporate_profiles_category_id_categories",
            "corporate_profiles",
            "categories",
            ["category_id"],
            ["id"],
        )


def downgrade() -> None:
    """Remove company_id and category_id columns from corporate_profiles table."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "corporate_profiles" not in inspector.get_table_names():
        print("corporate_profiles table does not exist, skipping downgrade")
        return

    columns = [col["name"] for col in inspector.get_columns("corporate_profiles")]

    if "company_id" in columns:
        op.drop_constraint(
            "fk_corporate_profiles_company_id_companies",
            "corporate_profiles",
            type_="foreignkey",
        )
        op.drop_column("corporate_profiles", "company_id")

    if "category_id" in columns:
        op.drop_constraint(
            "fk_corporate_profiles_category_id_categories",
            "corporate_profiles",
            type_="foreignkey",
        )
        op.drop_column("corporate_profiles", "category_id")


