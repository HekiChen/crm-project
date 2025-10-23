"""
Migration generator for CRUD entities.

Generates Alembic migration files for new entities using the migration template.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class MigrationGenerator:
    """
    Generates Alembic migration files for CRUD entities.

    Uses the migration template to create properly structured migration files
    with descriptive messages and revision IDs.
    """

    def __init__(
        self, alembic_dir: Optional[Path] = None, backend_dir: Optional[Path] = None
    ):
        """
        Initialize migration generator.

        Args:
            alembic_dir: Path to alembic directory (default: backend/alembic)
            backend_dir: Path to backend directory (default: backend)
        """
        if backend_dir is None:
            # Default to backend directory
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent

        if alembic_dir is None:
            alembic_dir = backend_dir / "alembic"

        self.alembic_dir = alembic_dir
        self.backend_dir = backend_dir
        self.versions_dir = alembic_dir / "versions"

    def _get_latest_revision(self) -> Optional[str]:
        """
        Get the latest migration revision ID.

        Returns:
            Latest revision ID or None if no migrations exist
        """
        if not self.versions_dir.exists():
            return None

        # Get all migration files
        migration_files = list(self.versions_dir.glob("*.py"))
        if not migration_files:
            return None

        # Sort by filename (they start with revision ID)
        migration_files.sort()

        # Read the last migration file to get its revision
        last_migration = migration_files[-1]
        content = last_migration.read_text()

        # Extract revision ID from the file (look for the actual variable assignment, not docstring)
        # Use negative lookbehind to avoid matching "down_revision"
        match = re.search(r"(?<!down_)revision\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            return match.group(1)

        return None

    def _generate_revision_id(self) -> str:
        """
        Generate a unique revision ID.

        Returns:
            12-character hex revision ID
        """
        import uuid

        return uuid.uuid4().hex[:12]

    def _create_migration_message(
        self, entity_name: str, operation: str = "create"
    ) -> str:
        """
        Create descriptive migration message.

        Args:
            entity_name: Entity name (e.g., "user")
            operation: Operation type (create, update, delete)

        Returns:
            Migration message
        """
        return f"{operation}_{entity_name}_table"

    def generate_migration(
        self,
        entity_name: str,
        migration_content: str,
        operation: str = "create",
    ) -> Tuple[Path, str]:
        """
        Generate migration file from template content.

        Args:
            entity_name: Entity name (e.g., "user")
            migration_content: Rendered migration template content
            operation: Operation type (create, update, delete)

        Returns:
            Tuple of (migration_file_path, revision_id)
        """
        # Generate revision ID
        revision_id = self._generate_revision_id()

        # Get latest revision as down_revision
        down_revision = self._get_latest_revision()

        # Create migration message
        message = self._create_migration_message(entity_name, operation)

        # Update migration content with correct revision IDs using regex
        # Replace revision = "None" (but not down_revision = "None")
        migration_content = re.sub(
            r'(?<!down_)revision\s*=\s*"None"',
            f'revision = "{revision_id}"',
            migration_content,
        )
        # Replace down_revision = "None"
        migration_content = re.sub(
            r'down_revision\s*=\s*"None"',
            f"down_revision = {repr(down_revision)}",
            migration_content,
        )

        # Create filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{revision_id}_{timestamp}_{message}.py"
        migration_path = self.versions_dir / filename

        # Ensure versions directory exists
        self.versions_dir.mkdir(parents=True, exist_ok=True)

        # Write migration file
        migration_path.write_text(migration_content)

        return migration_path, revision_id

    def generate_with_autogenerate(
        self,
        entity_name: str,
        message: Optional[str] = None,
    ) -> Tuple[Optional[Path], Optional[str]]:
        """
        Generate migration using alembic autogenerate.

        This runs `alembic revision --autogenerate` to automatically
        detect schema changes and generate migrations.

        Args:
            entity_name: Entity name for message
            message: Custom migration message (optional)

        Returns:
            Tuple of (migration_file_path, revision_id) or (None, None) on error
        """
        # Create migration message
        if message is None:
            message = self._create_migration_message(entity_name, "create")

        try:
            # Run alembic revision --autogenerate
            result = subprocess.run(
                ["alembic", "revision", "--autogenerate", "-m", message],
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse output to find generated migration file
            output = result.stdout

            # Look for "Generating ..." line
            match = re.search(r"Generating\s+(.+?\.py)", output)
            if match:
                migration_filename = match.group(1)
                # Extract just the filename (remove path)
                migration_filename = Path(migration_filename).name
                migration_path = self.versions_dir / migration_filename

                if migration_path.exists():
                    # Extract revision ID from filename
                    revision_match = re.match(r"([a-f0-9]+)_", migration_filename)
                    if revision_match:
                        revision_id = revision_match.group(1)
                        return migration_path, revision_id

            return None, None

        except subprocess.CalledProcessError as e:
            # Alembic command failed
            print(f"Error running alembic: {e.stderr}")
            return None, None
        except FileNotFoundError:
            # Alembic not installed or not in PATH
            print("Error: alembic command not found. Is alembic installed?")
            return None, None

    def list_migrations(self) -> list[Path]:
        """
        List all migration files.

        Returns:
            List of migration file paths, sorted by creation time
        """
        if not self.versions_dir.exists():
            return []

        migration_files = list(self.versions_dir.glob("*.py"))
        # Filter out __pycache__ and __init__.py
        migration_files = [
            f for f in migration_files if f.name not in ["__init__.py", "__pycache__"]
        ]
        migration_files.sort()

        return migration_files

    def get_migration_info(self, migration_path: Path) -> dict:
        """
        Extract information from a migration file.

        Args:
            migration_path: Path to migration file

        Returns:
            Dictionary with revision, down_revision, and message
        """
        content = migration_path.read_text()

        info = {
            "filename": migration_path.name,
            "path": migration_path,
            "revision": None,
            "down_revision": None,
            "message": None,
        }

        # Extract revision
        match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            info["revision"] = match.group(1)

        # Extract down_revision
        match = re.search(r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", content)
        if match:
            info["down_revision"] = match.group(1)

        # Extract message from filename
        match = re.search(r"_\d{8}_\d{6}_(.+)\.py$", migration_path.name)
        if match:
            info["message"] = match.group(1)

        return info
