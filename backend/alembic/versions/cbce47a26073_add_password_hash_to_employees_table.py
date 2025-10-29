"""Add password_hash to employees table

Revision ID: cbce47a26073
Revises: 599e1afc469a
Create Date: 2025-10-29 11:57:39.364403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbce47a26073'
down_revision = '599e1afc469a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash column to employees table
    op.add_column(
        'employees',
        sa.Column('password_hash', sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    # Remove password_hash column from employees table
    op.drop_column('employees', 'password_hash')