"""
Router registration in main.py.

Parses app/main.py and adds router imports and registrations
for generated CRUD entities.
"""

import re
from pathlib import Path
from typing import List, Tuple, Optional


class RouterRegistration:
    """
    Manages router registration in FastAPI main.py.

    Parses the main.py file, adds router imports and include_router calls,
    while avoiding duplicates and maintaining code formatting.
    """

    def __init__(self, main_py_path: Optional[Path] = None):
        """
        Initialize router registration.

        Args:
            main_py_path: Path to main.py file (default: backend/app/main.py)
        """
        if main_py_path is None:
            # Default to app/main.py relative to this file
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent
            main_py_path = backend_dir / "app" / "main.py"

        self.main_py_path = main_py_path
        self.content = ""
        self.lines: List[str] = []

    def load(self) -> None:
        """Load main.py content."""
        if not self.main_py_path.exists():
            raise FileNotFoundError(f"main.py not found at {self.main_py_path}")

        self.content = self.main_py_path.read_text()
        self.lines = self.content.split("\n")

    def save(self) -> None:
        """Save modified content back to main.py."""
        self.content = "\n".join(self.lines)
        self.main_py_path.write_text(self.content)

    def _find_import_section_end(self) -> int:
        """
        Find the line number where imports end.
        
        Handles multi-line imports with parentheses.

        Returns:
            Line index where imports end
        """
        # Find the last import statement before other code
        last_import_idx = -1
        in_multiline_import = False

        for i, line in enumerate(self.lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            # Check if we're entering/exiting a multi-line import
            if "(" in line and ("import " in line or "from " in line):
                in_multiline_import = True
                last_import_idx = i
            elif in_multiline_import:
                last_import_idx = i
                if ")" in line:
                    in_multiline_import = False
            # Check if it's a single-line import
            elif stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i
            # Stop when we hit non-import code (except docstrings)
            elif (
                last_import_idx >= 0
                and not in_multiline_import
                and not stripped.startswith('"""')
                and not stripped.startswith("'''")
            ):
                break

        return last_import_idx

    def _find_router_registration_section(self) -> Tuple[int, int]:
        """
        Find the section where routers are registered.

        Returns:
            Tuple of (start_line, end_line) for router registration section
        """
        start_idx = -1
        end_idx = -1

        for i, line in enumerate(self.lines):
            stripped = line.strip()

            # Look for "# Include routers" comment or first include_router call
            if "# Include routers" in line or stripped.startswith(
                "app.include_router("
            ):
                if start_idx == -1:
                    start_idx = i
                end_idx = i

        return start_idx, end_idx

    def _router_import_exists(self, entity_plural: str) -> bool:
        """
        Check if router import already exists.

        Args:
            entity_plural: Plural entity name (e.g., "users")

        Returns:
            True if import exists
        """
        import_pattern = (
            f"from app.api.{entity_plural} import router as {entity_plural}_router"
        )
        return any(import_pattern in line for line in self.lines)

    def _router_registration_exists(self, entity_plural: str) -> bool:
        """
        Check if router registration already exists.

        Args:
            entity_plural: Plural entity name (e.g., "users")

        Returns:
            True if registration exists
        """
        # Check for include_router call with this router
        registration_pattern = f"app.include_router({entity_plural}_router"
        return any(registration_pattern in line for line in self.lines)

    def _add_import(self, entity_plural: str) -> None:
        """
        Add router import statement.

        Args:
            entity_plural: Plural entity name (e.g., "users")
        """
        # Find where to insert (after existing router imports or at end of imports)
        insert_idx = self._find_import_section_end()

        if insert_idx == -1:
            raise ValueError("Could not find import section in main.py")

        # Create import statement
        import_statement = (
            f"from app.api.{entity_plural} import router as {entity_plural}_router"
        )

        # Insert after the last import
        self.lines.insert(insert_idx + 1, import_statement)

    def _get_router_prefix(self, entity_plural: str) -> Optional[str]:
        """
        Get the prefix defined in the router file.
        
        Args:
            entity_plural: Plural entity name (e.g., "users")
            
        Returns:
            Router prefix if found, None otherwise
        """
        # Find the router file
        router_file = self.main_py_path.parent / "api" / entity_plural / "__init__.py"
        if not router_file.exists():
            return None
            
        content = router_file.read_text()
        
        # Look for APIRouter(prefix="/something")
        match = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
            
        return None

    def _add_registration(
        self, entity_name: str, entity_plural: str, api_prefix: str = "/api/v1"
    ) -> None:
        """
        Add router registration call.
        
        Detects if router already has a prefix to avoid duplication.

        Args:
            entity_name: Singular entity name (e.g., "user")
            entity_plural: Plural entity name (e.g., "users")
            api_prefix: API prefix (default: "/api/v1")
        """
        # Find router registration section
        start_idx, end_idx = self._find_router_registration_section()

        if start_idx == -1:
            raise ValueError("Could not find router registration section in main.py")

        # Check if router already has a prefix
        router_prefix = self._get_router_prefix(entity_plural)
        
        if router_prefix:
            # Router already has a prefix, only use the base API prefix
            registration = f'app.include_router({entity_plural}_router, prefix="{api_prefix}", tags=["{entity_plural}"])'
        else:
            # Router doesn't have a prefix, include entity-specific prefix
            registration = f'app.include_router({entity_plural}_router, prefix="{api_prefix}/{entity_plural}", tags=["{entity_plural}"])'

        # Insert after the last router registration
        self.lines.insert(end_idx + 1, registration)

    def register_router(
        self,
        entity_name: str,
        entity_plural: str,
        api_prefix: str = "/api/v1",
        skip_if_exists: bool = True,
    ) -> bool:
        """
        Register a router in main.py.

        Args:
            entity_name: Singular entity name (e.g., "user")
            entity_plural: Plural entity name (e.g., "users")
            api_prefix: API prefix (default: "/api/v1")
            skip_if_exists: Skip if router already registered

        Returns:
            True if router was registered, False if skipped

        Raises:
            ValueError: If import or registration already exists and skip_if_exists is False
        """
        # Load file
        self.load()

        # Check if already exists
        import_exists = self._router_import_exists(entity_plural)
        registration_exists = self._router_registration_exists(entity_plural)

        if import_exists and registration_exists:
            if skip_if_exists:
                return False
            else:
                raise ValueError(
                    f"Router {entity_plural}_router already registered in main.py"
                )

        # Add import if needed
        if not import_exists:
            self._add_import(entity_plural)

        # Add registration if needed
        if not registration_exists:
            self._add_registration(entity_name, entity_plural, api_prefix)

        # Save changes
        self.save()

        return True

    def unregister_router(self, entity_plural: str) -> bool:
        """
        Remove router registration from main.py.

        Args:
            entity_plural: Plural entity name (e.g., "users")

        Returns:
            True if router was unregistered, False if not found
        """
        # Load file
        self.load()

        # Find and remove import
        import_pattern = (
            f"from app.api.{entity_plural} import router as {entity_plural}_router"
        )
        import_removed = False
        for i, line in enumerate(self.lines):
            if import_pattern in line:
                self.lines.pop(i)
                import_removed = True
                break

        # Find and remove registration
        registration_pattern = f"app.include_router({entity_plural}_router"
        registration_removed = False
        for i, line in enumerate(self.lines):
            if registration_pattern in line:
                self.lines.pop(i)
                registration_removed = True
                break

        # Save if anything was removed
        if import_removed or registration_removed:
            self.save()
            return True

        return False

    def list_registered_routers(self) -> List[str]:
        """
        List all registered routers.

        Returns:
            List of registered router names (plural form)
        """
        # Load file
        self.load()

        routers = []

        # Find all include_router calls
        for line in self.lines:
            match = re.search(r"app\.include_router\((\w+)_router", line)
            if match:
                router_name = match.group(1)
                routers.append(router_name)

        return routers
