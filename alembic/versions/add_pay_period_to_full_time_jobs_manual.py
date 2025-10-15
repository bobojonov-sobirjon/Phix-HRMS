"""add_pay_period_to_full_time_jobs

Revision ID: add_pay_period_manual
Revises: cd18a6a412b1
Create Date: 2025-10-15 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_pay_period_manual'
down_revision: Union[str, Sequence[str], None] = 'cd18a6a412b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the PayPeriod enum type
    pay_period_enum = postgresql.ENUM(
        'PER_HOUR', 'PER_DAY', 'PER_WEEK', 'PER_MONTH', 'PER_YEAR',
        name='payperiod'
    )
    pay_period_enum.create(op.get_bind())
    
    # Add the pay_period column to full_time_jobs table
    op.add_column('full_time_jobs', 
        sa.Column('pay_period', pay_period_enum, nullable=False, server_default='PER_MONTH')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the pay_period column
    op.drop_column('full_time_jobs', 'pay_period')
    
    # Drop the PayPeriod enum type
    pay_period_enum = postgresql.ENUM(
        'PER_HOUR', 'PER_DAY', 'PER_WEEK', 'PER_MONTH', 'PER_YEAR',
        name='payperiod'
    )
    pay_period_enum.drop(op.get_bind())
