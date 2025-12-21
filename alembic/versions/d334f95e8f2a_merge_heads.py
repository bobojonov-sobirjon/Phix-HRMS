"""merge_heads

Revision ID: d334f95e8f2a
Revises: b7294e7b7b78, remove_company_name_industry_manual
Create Date: 2025-12-19 19:57:28.869292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd334f95e8f2a'
down_revision: Union[str, Sequence[str], None] = ('b7294e7b7b78', 'remove_company_name_industry_manual')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
