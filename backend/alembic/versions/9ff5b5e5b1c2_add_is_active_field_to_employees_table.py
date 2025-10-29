"""Add is_active field to employees table

Revision ID: 9ff5b5e5b1c2
Revises: cbce47a26073
Create Date: 2025-10-29 13:11:18.745432

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9ff5b5e5b1c2'
down_revision = 'cbce47a26073'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_active column to employees table with default value True
    op.add_column('employees', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    # Remove is_active column from employees table
    op.drop_column('employees', 'is_active')