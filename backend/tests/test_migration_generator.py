"""
Tests for MigrationGenerator class.
"""
import re
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cli.migration_generator import MigrationGenerator


# Sample migration content
SAMPLE_MIGRATION_CONTENT = '''"""
create_user_table migration.

Revision ID: None
Revises: None
Create Date: 2025-01-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "None"
down_revision = "None"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('users')
'''


@pytest.fixture
def temp_alembic_dir(tmp_path):
    """Create temporary alembic directory structure."""
    alembic_dir = tmp_path / "alembic"
    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir(parents=True)
    return alembic_dir


@pytest.fixture
def migration_generator(temp_alembic_dir, tmp_path):
    """Create MigrationGenerator instance with temp directory."""
    return MigrationGenerator(alembic_dir=temp_alembic_dir, backend_dir=tmp_path)


def test_init_default_paths():
    """Test initialization with default paths."""
    generator = MigrationGenerator()
    
    assert generator.alembic_dir.exists()
    assert generator.backend_dir.exists()
    assert generator.versions_dir == generator.alembic_dir / "versions"


def test_get_latest_revision_empty(migration_generator):
    """Test getting latest revision when no migrations exist."""
    revision = migration_generator._get_latest_revision()
    assert revision is None


def test_get_latest_revision_with_migrations(migration_generator, temp_alembic_dir):
    """Test getting latest revision with existing migrations."""
    versions_dir = temp_alembic_dir / "versions"
    
    # Create first migration
    migration1 = versions_dir / "abc123_20250101_120000_create_user_table.py"
    migration1.write_text('revision = "abc123"\ndown_revision = None')
    
    # Create second migration
    migration2 = versions_dir / "def456_20250102_120000_create_product_table.py"
    migration2.write_text('revision = "def456"\ndown_revision = "abc123"')
    
    revision = migration_generator._get_latest_revision()
    assert revision == "def456"


def test_generate_revision_id(migration_generator):
    """Test revision ID generation."""
    revision_id = migration_generator._generate_revision_id()
    
    assert len(revision_id) == 12
    assert re.match(r'^[a-f0-9]{12}$', revision_id)


def test_create_migration_message(migration_generator):
    """Test migration message creation."""
    message = migration_generator._create_migration_message("user", "create")
    assert message == "create_user_table"
    
    message = migration_generator._create_migration_message("product", "update")
    assert message == "update_product_table"


def test_generate_migration(migration_generator, temp_alembic_dir):
    """Test migration file generation."""
    migration_path, revision_id = migration_generator.generate_migration(
        entity_name="user",
        migration_content=SAMPLE_MIGRATION_CONTENT,
        operation="create",
    )
    
    # Check file was created
    assert migration_path.exists()
    assert migration_path.parent == temp_alembic_dir / "versions"
    
    # Check filename format
    assert re.match(r'^[a-f0-9]{12}_\d{8}_\d{6}_create_user_table\.py$', migration_path.name)
    
    # Check revision ID
    assert len(revision_id) == 12
    
    # Check content
    content = migration_path.read_text()
    assert f'revision = "{revision_id}"' in content
    assert 'down_revision = None' in content
    assert 'def upgrade()' in content
    assert 'def downgrade()' in content


def test_generate_migration_with_down_revision(migration_generator, temp_alembic_dir):
    """Test migration generation with existing migrations."""
    versions_dir = temp_alembic_dir / "versions"
    
    # Create first migration
    migration1 = versions_dir / "abc123_20250101_120000_create_user_table.py"
    migration1.write_text('revision = "abc123"\ndown_revision = None')
    
    # Generate second migration
    migration_path, revision_id = migration_generator.generate_migration(
        entity_name="product",
        migration_content=SAMPLE_MIGRATION_CONTENT,
        operation="create",
    )
    
    # Check down_revision points to first migration (with single quotes from repr)
    content = migration_path.read_text()
    assert "down_revision = 'abc123'" in content


def test_generate_with_autogenerate_success(migration_generator, temp_alembic_dir):
    """Test autogenerate migration success."""
    # Mock subprocess.run
    mock_result = MagicMock()
    mock_result.stdout = "Generating /path/to/abc123_20250101_120000_create_user_table.py...done"
    mock_result.returncode = 0
    
    # Create the migration file that alembic would create
    versions_dir = temp_alembic_dir / "versions"
    migration_file = versions_dir / "abc123_20250101_120000_create_user_table.py"
    migration_file.write_text('revision = "abc123"')
    
    with patch('subprocess.run', return_value=mock_result):
        migration_path, revision_id = migration_generator.generate_with_autogenerate("user")
    
    assert migration_path == migration_file
    assert revision_id == "abc123"


def test_generate_with_autogenerate_command_error(migration_generator):
    """Test autogenerate when alembic command fails."""
    # Mock subprocess.run to raise CalledProcessError
    with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'alembic', stderr='Error')):
        migration_path, revision_id = migration_generator.generate_with_autogenerate("user")
    
    assert migration_path is None
    assert revision_id is None


def test_generate_with_autogenerate_not_found(migration_generator):
    """Test autogenerate when alembic not installed."""
    # Mock subprocess.run to raise FileNotFoundError
    with patch('subprocess.run', side_effect=FileNotFoundError()):
        migration_path, revision_id = migration_generator.generate_with_autogenerate("user")
    
    assert migration_path is None
    assert revision_id is None


def test_generate_with_autogenerate_custom_message(migration_generator, temp_alembic_dir):
    """Test autogenerate with custom message."""
    mock_result = MagicMock()
    mock_result.stdout = "Generating /path/to/abc123_20250101_120000_custom_migration.py...done"
    mock_result.returncode = 0
    
    versions_dir = temp_alembic_dir / "versions"
    migration_file = versions_dir / "abc123_20250101_120000_custom_migration.py"
    migration_file.write_text('revision = "abc123"')
    
    with patch('subprocess.run', return_value=mock_result):
        migration_path, revision_id = migration_generator.generate_with_autogenerate(
            "user",
            message="custom_migration"
        )
    
    assert migration_path == migration_file
    assert revision_id == "abc123"


def test_list_migrations_empty(migration_generator):
    """Test listing migrations when none exist."""
    migrations = migration_generator.list_migrations()
    assert migrations == []


def test_list_migrations(migration_generator, temp_alembic_dir):
    """Test listing migrations."""
    versions_dir = temp_alembic_dir / "versions"
    
    # Create migrations
    migration1 = versions_dir / "abc123_20250101_120000_create_user_table.py"
    migration1.write_text('revision = "abc123"')
    
    migration2 = versions_dir / "def456_20250102_120000_create_product_table.py"
    migration2.write_text('revision = "def456"')
    
    migrations = migration_generator.list_migrations()
    
    assert len(migrations) == 2
    assert migrations[0].name == "abc123_20250101_120000_create_user_table.py"
    assert migrations[1].name == "def456_20250102_120000_create_product_table.py"


def test_get_migration_info(migration_generator, temp_alembic_dir):
    """Test extracting migration information."""
    versions_dir = temp_alembic_dir / "versions"
    
    # Create migration
    migration = versions_dir / "abc123_20250101_120000_create_user_table.py"
    migration.write_text('''
revision = "abc123"
down_revision = "xyz789"

def upgrade():
    pass

def downgrade():
    pass
''')
    
    info = migration_generator.get_migration_info(migration)
    
    assert info["filename"] == "abc123_20250101_120000_create_user_table.py"
    assert info["path"] == migration
    assert info["revision"] == "abc123"
    assert info["down_revision"] == "xyz789"
    assert info["message"] == "create_user_table"


def test_get_migration_info_no_down_revision(migration_generator, temp_alembic_dir):
    """Test extracting info from migration without down_revision."""
    versions_dir = temp_alembic_dir / "versions"
    
    migration = versions_dir / "abc123_20250101_120000_initial.py"
    migration.write_text('revision = "abc123"\ndown_revision = None')
    
    info = migration_generator.get_migration_info(migration)
    
    assert info["revision"] == "abc123"
    assert info["down_revision"] is None


def test_multiple_migrations_chain(migration_generator, temp_alembic_dir):
    """Test generating multiple migrations in sequence."""
    versions_dir = temp_alembic_dir / "versions"
    
    # Generate first migration
    path1, rev1 = migration_generator.generate_migration(
        entity_name="user",
        migration_content=SAMPLE_MIGRATION_CONTENT,
        operation="create",
    )
    
    assert path1.exists()
    content1 = path1.read_text()
    assert 'down_revision = None' in content1
    
    # Generate second migration
    path2, rev2 = migration_generator.generate_migration(
        entity_name="product",
        migration_content=SAMPLE_MIGRATION_CONTENT,
        operation="create",
    )
    
    assert path2.exists()
    content2 = path2.read_text()
    # Check with single quotes from repr
    assert f"down_revision = '{rev1}'" in content2
    
    # Generate third migration
    path3, rev3 = migration_generator.generate_migration(
        entity_name="order",
        migration_content=SAMPLE_MIGRATION_CONTENT,
        operation="create",
    )
    
    assert path3.exists()
    content3 = path3.read_text()
    # Check with single quotes from repr
    assert f"down_revision = '{rev2}'" in content3


# Import subprocess for the test
import subprocess
