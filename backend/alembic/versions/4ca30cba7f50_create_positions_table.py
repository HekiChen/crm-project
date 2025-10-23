"""create_positions_table

Revision ID: 4ca30cba7f50
Revises: 05766dd4de23
Create Date: 2025-10-23 11:14:13.893307

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ca30cba7f50'
down_revision = '05766dd4de23'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create positions table."""
    op.create_table(
        'positions',
        # Primary key
        sa.Column('id', sa.UUID(), nullable=False),
        
        # Core fields
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        
        # Timestamp fields (from BaseModel)
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Soft delete fields (from BaseModel)
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        
        # Audit fields (from BaseModel)
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        
        # Primary key constraint
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes
    op.create_index('ix_positions_id', 'positions', ['id'], unique=False)
    op.create_index('ix_positions_name', 'positions', ['name'], unique=False)
    op.create_index('ix_positions_code', 'positions', ['code'], unique=False)
    op.create_index('ix_positions_level', 'positions', ['level'], unique=False)
    op.create_index('ix_positions_department_id', 'positions', ['department_id'], unique=False)
    op.create_index('ix_positions_is_active', 'positions', ['is_active'], unique=False)
    op.create_index('ix_positions_is_deleted', 'positions', ['is_deleted'], unique=False)
    
    # Create unique constraint on (code, is_deleted) to allow code reuse after soft deletion
    op.create_index('ix_positions_code_is_deleted', 'positions', ['code', 'is_deleted'], unique=True)


def downgrade() -> None:
    """Drop positions table."""
    # Drop indexes
    op.drop_index('ix_positions_code_is_deleted', table_name='positions')
    op.drop_index('ix_positions_is_deleted', table_name='positions')
    op.drop_index('ix_positions_is_active', table_name='positions')
    op.drop_index('ix_positions_department_id', table_name='positions')
    op.drop_index('ix_positions_level', table_name='positions')
    op.drop_index('ix_positions_code', table_name='positions')
    op.drop_index('ix_positions_name', table_name='positions')
    op.drop_index('ix_positions_id', table_name='positions')
    
    # Drop table
    op.drop_table('positions')
