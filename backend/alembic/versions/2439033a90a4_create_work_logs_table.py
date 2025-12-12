"""create_work_logs_table

Revision ID: 2439033a90a4
Revises: 1aad62b084ab
Create Date: 2025-12-12 15:02:34.659897

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2439033a90a4'
down_revision = '1aad62b084ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create work_logs table
    op.create_table(
        'work_logs',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(length=32), nullable=True),
        sa.Column('updated_by_id', sa.String(length=32), nullable=True),
        sa.Column('employee_id', sa.String(length=32), nullable=False),
        sa.Column('log_type', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', name='logtype'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('progress', sa.Text(), nullable=False),
        sa.Column('issues', sa.Text(), nullable=True),
        sa.Column('plans', sa.Text(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('rated_by_id', sa.String(length=32), nullable=True),
        sa.Column('rated_at', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['rated_by_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_logs_employee_id'), 'work_logs', ['employee_id'], unique=False)
    op.create_index(op.f('ix_work_logs_log_type'), 'work_logs', ['log_type'], unique=False)
    op.create_index(op.f('ix_work_logs_start_date'), 'work_logs', ['start_date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_work_logs_start_date'), table_name='work_logs')
    op.drop_index(op.f('ix_work_logs_log_type'), table_name='work_logs')
    op.drop_index(op.f('ix_work_logs_employee_id'), table_name='work_logs')
    op.drop_table('work_logs')