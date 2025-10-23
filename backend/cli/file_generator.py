"""
File generator for CRUD scaffolding.

Loads Jinja2 templates, renders them with entity-specific data,
and writes generated files to disk.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from cli.field_parser import FieldDefinition
from cli.router_registration import RouterRegistration
from cli.migration_generator import MigrationGenerator


class FileGenerator:
    """
    Generator for CRUD scaffolding files.

    Loads Jinja2 templates from templates/crud/ directory,
    renders them with entity-specific data, and writes
    generated files to the appropriate locations.
    """

    def __init__(
        self, template_dir: Optional[Path] = None, output_dir: Optional[Path] = None
    ):
        """
        Initialize file generator.

        Args:
            template_dir: Directory containing Jinja2 templates (default: backend/templates/crud)
            output_dir: Base output directory (default: backend)
        """
        if template_dir is None:
            # Default to templates/crud relative to this file
            current_file = Path(__file__).resolve()
            backend_dir = current_file.parent.parent
            template_dir = backend_dir / "templates" / "crud"

        if output_dir is None:
            # Default to backend directory
            current_file = Path(__file__).resolve()
            output_dir = current_file.parent.parent

        self.template_dir = template_dir
        self.output_dir = output_dir

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.generated_files: List[Path] = []

    def _to_snake_case(self, name: str) -> str:
        """
        Convert PascalCase or camelCase to snake_case.

        Args:
            name: Name to convert

        Returns:
            snake_case version
        """
        # Insert underscore before uppercase letters
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # Insert underscore before uppercase letters preceded by lowercase
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()

    def _to_pascal_case(self, name: str) -> str:
        """
        Convert snake_case to PascalCase.

        Args:
            name: Name to convert

        Returns:
            PascalCase version
        """
        return "".join(word.capitalize() for word in name.split("_"))

    def _pluralize(self, word: str) -> str:
        """
        Simple pluralization of English words.

        Args:
            word: Word to pluralize

        Returns:
            Pluralized word
        """
        if word.endswith("s"):
            return f"{word}es"
        elif word.endswith("y"):
            return f"{word[:-1]}ies"
        elif word.endswith("ch") or word.endswith("sh"):
            return f"{word}es"
        else:
            return f"{word}s"

    def _prepare_context(
        self,
        entity_name: str,
        fields: List[FieldDefinition],
        soft_delete: bool = True,
        timestamps: bool = True,
        audit: bool = True,
        domain: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Prepare template context from entity data.

        Args:
            entity_name: Entity name (snake_case, e.g., "user", "employee")
            fields: List of field definitions
            soft_delete: Enable soft delete
            timestamps: Enable timestamps
            audit: Enable audit fields
            domain: CRM domain type (employee, customer, generic)

        Returns:
            Context dictionary for template rendering
        """
        # Convert names
        entity_snake = self._to_snake_case(entity_name)
        entity_class = self._to_pascal_case(entity_snake)
        table_name = self._pluralize(entity_snake)
        endpoint_prefix = table_name

        # Determine domain mixins
        domain_mixins = []
        if domain == "employee":
            domain_mixins = ["PersonMixin", "ContactMixin", "EmployeeMixin"]
        elif domain == "customer":
            domain_mixins = ["PersonMixin", "ContactMixin", "CustomerMixin"]

        # Check if we need custom types
        use_custom_types = any(
            field.sqlalchemy_type in ["EmailType", "PhoneNumberType", "MoneyType"]
            for field in fields
        )

        # Prepare field sample values for tests
        for field in fields:
            # Set doc if not provided
            if not hasattr(field, "doc") or field.doc is None:
                field.doc = f"The {field.name} field"

            # Generate sample values for tests
            if field.python_type == "str":
                field.sample_value = f'"{field.name}_value"'
                field.sample_value_pattern = f'f"{field.name}_{{i}}"'
                field.updated_sample_value = f'"{field.name}_updated"'
            elif field.python_type == "int":
                field.sample_value = "123"
                field.sample_value_pattern = "i"
                field.updated_sample_value = "456"
            elif field.python_type == "float":
                field.sample_value = "123.45"
                field.sample_value_pattern = "float(i)"
                field.updated_sample_value = "456.78"
            elif field.python_type == "Decimal":
                field.sample_value = 'Decimal("123.45")'
                field.sample_value_pattern = 'Decimal(f"{i}.99")'
                field.updated_sample_value = 'Decimal("456.78")'
            elif field.python_type == "bool":
                field.sample_value = "True"
                field.sample_value_pattern = "bool(i % 2)"
                field.updated_sample_value = "False"
            elif field.python_type == "date":
                field.sample_value = "date(2025, 1, 1)"
                field.sample_value_pattern = "date(2025, 1, i)"
                field.updated_sample_value = "date(2025, 12, 31)"
            elif field.python_type == "datetime":
                field.sample_value = "datetime(2025, 1, 1, 12, 0, 0)"
                field.sample_value_pattern = "datetime(2025, 1, i, 12, 0, 0)"
                field.updated_sample_value = "datetime(2025, 12, 31, 23, 59, 59)"
            else:
                field.sample_value = "None"
                field.sample_value_pattern = "None"
                field.updated_sample_value = "None"

        # Build repr_fields for __repr__ method
        repr_fields_list = []
        for field in fields[:2]:  # First 2 fields
            if not field.is_nullable:
                repr_fields_list.append(f"{field.name}='{{self.{field.name}}}'")
        repr_fields = ", ".join(repr_fields_list) if repr_fields_list else ""

        # Extract foreign keys for migration
        foreign_keys = []
        for field in fields:
            if field.is_foreign_key and field.foreign_table:
                foreign_keys.append(
                    {
                        "column": field.name,
                        "target_table": field.foreign_table,
                    }
                )

        # Extract unique constraints
        unique_constraints = [field.name for field in fields if field.is_unique]

        # Extract indexed fields
        indexed_fields = [field.name for field in fields if field.is_indexed]

        # Check if any field has Decimal type
        has_decimal_fields = any(field.python_type == "Decimal" for field in fields)

        # Build context
        context = {
            "entity_name": entity_snake,
            "entity_class": entity_class,
            "table_name": table_name,
            "endpoint_prefix": endpoint_prefix,
            "fields": fields,
            "soft_delete": soft_delete,
            "timestamps": timestamps,
            "audit": audit,
            "domain_mixins": domain_mixins,
            "use_custom_types": use_custom_types,
            "relationships": [],  # Can be extended in future
            "repr_fields": repr_fields,
            "has_validators": True,  # Placeholder for future
            "validation_tests": True,  # Placeholder for future
            "description": None,  # Can be provided by user in future
            "foreign_keys": foreign_keys,
            "unique_constraints": unique_constraints,
            "indexed_fields": indexed_fields,
            "has_decimal_fields": has_decimal_fields,
            # Migration-specific
            "migration_message": f"Create {entity_snake} table",
            "revision_id": uuid4().hex[:12],
            "down_revision": "None",  # Will be updated by migration generator
            "create_date": datetime.utcnow().isoformat(),
        }

        return context

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with context.

        Args:
            template_name: Template filename (e.g., "model.py.jinja2")
            context: Template context

        Returns:
            Rendered template string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def _ensure_directory(self, file_path: Path) -> None:
        """
        Ensure directory exists for file path.

        Args:
            file_path: File path to create directory for
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_file(
        self,
        file_path: Path,
        content: str,
        backup_existing: bool = True,
    ) -> None:
        """
        Write content to file with optional backup.

        Args:
            file_path: Path to write to
            content: Content to write
            backup_existing: Whether to backup existing file

        Raises:
            FileExistsError: If file exists and backup_existing is False
        """
        # Check if file exists
        if file_path.exists():
            if backup_existing:
                # Create backup
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                backup_path.write_text(file_path.read_text())
            else:
                raise FileExistsError(f"File already exists: {file_path}")

        # Ensure directory exists
        self._ensure_directory(file_path)

        # Write file
        file_path.write_text(content)
        self.generated_files.append(file_path)

    def generate_model(
        self,
        entity_name: str,
        fields: List[FieldDefinition],
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate model file.

        Args:
            entity_name: Entity name
            fields: Field definitions
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("model.py.jinja2", context)
        file_path = self.output_dir / "app" / "models" / f"{entity_name}.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_service(
        self,
        entity_name: str,
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate service file.

        Args:
            entity_name: Entity name
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("service.py.jinja2", context)
        file_path = self.output_dir / "app" / "services" / f"{entity_name}_service.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_schemas(
        self,
        entity_name: str,
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate schemas file.

        Args:
            entity_name: Entity name
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("schemas.py.jinja2", context)
        file_path = self.output_dir / "app" / "schemas" / f"{entity_name}_schemas.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_api(
        self,
        endpoint_prefix: str,
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate API router file.

        Args:
            endpoint_prefix: API endpoint prefix (plural form)
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("api.py.jinja2", context)
        file_path = self.output_dir / "app" / "api" / f"{endpoint_prefix}.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_test_api(
        self,
        endpoint_prefix: str,
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate API test file.

        Args:
            endpoint_prefix: API endpoint prefix (plural form)
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("test_api.py.jinja2", context)
        file_path = self.output_dir / "tests" / f"test_{endpoint_prefix}_api.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_test_service(
        self,
        endpoint_prefix: str,
        context: Dict[str, Any],
        backup_existing: bool = True,
    ) -> Path:
        """
        Generate service test file.

        Args:
            endpoint_prefix: API endpoint prefix (plural form)
            context: Template context
            backup_existing: Backup existing file

        Returns:
            Path to generated file
        """
        content = self._render_template("test_service.py.jinja2", context)
        file_path = self.output_dir / "tests" / f"test_{endpoint_prefix}_service.py"
        self._write_file(file_path, content, backup_existing)
        return file_path

    def generate_all(
        self,
        entity_name: str,
        fields: List[FieldDefinition],
        soft_delete: bool = True,
        timestamps: bool = True,
        audit: bool = True,
        domain: Optional[str] = None,
        backup_existing: bool = True,
        register_router: bool = True,
        api_prefix: str = "/api/v1",
        generate_migration: bool = True,
    ) -> Tuple[List[Path], Optional[Path]]:
        """
        Generate all files for an entity.

        Args:
            entity_name: Entity name (snake_case)
            fields: List of field definitions
            soft_delete: Enable soft delete
            timestamps: Enable timestamps
            audit: Enable audit fields
            domain: CRM domain type
            backup_existing: Backup existing files
            register_router: Register router in main.py
            api_prefix: API prefix for router registration
            generate_migration: Generate Alembic migration file

        Returns:
            Tuple of (list of generated file paths, migration file path or None)
        """
        # Prepare context
        context = self._prepare_context(
            entity_name, fields, soft_delete, timestamps, audit, domain
        )

        # Reset generated files list
        self.generated_files = []

        # Generate all files
        self.generate_model(entity_name, fields, context, backup_existing)
        self.generate_service(entity_name, context, backup_existing)
        self.generate_schemas(entity_name, context, backup_existing)
        self.generate_api(context["endpoint_prefix"], context, backup_existing)
        self.generate_test_api(context["endpoint_prefix"], context, backup_existing)
        self.generate_test_service(context["endpoint_prefix"], context, backup_existing)

        # Register router in main.py if requested
        if register_router:
            main_py_path = self.output_dir / "app" / "main.py"
            if main_py_path.exists():
                router_reg = RouterRegistration(main_py_path=main_py_path)
                router_reg.register_router(
                    entity_name=entity_name,
                    entity_plural=context["endpoint_prefix"],
                    api_prefix=api_prefix,
                    skip_if_exists=True,
                )

        # Generate migration file if requested
        migration_path = None
        if generate_migration:
            # Render migration template
            migration_content = self._render_template("migration.py.jinja2", context)

            # Generate migration file
            migration_gen = MigrationGenerator(backend_dir=self.output_dir)
            migration_path, revision_id = migration_gen.generate_migration(
                entity_name=entity_name,
                migration_content=migration_content,
                operation="create",
            )

        return self.generated_files, migration_path
