"""
Field definition parser for CRUD generator.

Parses field definitions from CLI arguments and converts them to
structured data for template rendering.

Format: "name:type:constraints" or "name:type"
Example: "email:str:unique", "age:int", "price:decimal:nullable"
"""

from dataclasses import dataclass
from typing import Any, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, Float


# Type mapping from string shorthand to SQLAlchemy types
TYPE_MAPPING = {
    # String types
    "str": String,
    "string": String,
    "text": Text,
    # Numeric types
    "int": Integer,
    "integer": Integer,
    "float": Float,
    "decimal": Numeric,
    "money": Numeric,  # Numeric(15, 2) for money
    # Boolean
    "bool": Boolean,
    "boolean": Boolean,
    # Date/Time
    "date": Date,
    "datetime": DateTime,
    "timestamp": DateTime,
    # Special CRM types (will map to custom types)
    "email": "EmailType",
    "phone": "PhoneNumberType",
}

# Default string length
DEFAULT_STRING_LENGTH = 255


@dataclass
class FieldConstraint:
    """Represents a constraint on a field."""

    name: str
    value: Optional[Any] = None


@dataclass
class FieldDefinition:
    """
    Structured representation of a field definition.

    Attributes:
        name: Field name (snake_case)
        type: Python/SQLAlchemy type name
        sqlalchemy_type: SQLAlchemy type for model generation
        python_type: Python type hint for schemas
        constraints: List of constraints (unique, nullable, etc.)
        is_foreign_key: Whether this is a foreign key field
        foreign_table: Table name for foreign key (if applicable)
        length: String length for String types
        precision: Numeric precision for Decimal types
        scale: Numeric scale for Decimal types
        doc: Documentation string for the field
        sample_value: Sample value for tests
        sample_value_pattern: Pattern for generating multiple sample values
        updated_sample_value: Updated value for update tests
    """

    name: str
    type: str
    sqlalchemy_type: str
    python_type: str
    constraints: List[FieldConstraint]
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    doc: Optional[str] = None
    sample_value: Optional[str] = None
    sample_value_pattern: Optional[str] = None
    updated_sample_value: Optional[str] = None

    @property
    def is_unique(self) -> bool:
        """Check if field has unique constraint."""
        return any(c.name == "unique" for c in self.constraints)

    @property
    def is_nullable(self) -> bool:
        """Check if field is nullable."""
        return any(c.name == "nullable" for c in self.constraints)

    @property
    def is_indexed(self) -> bool:
        """Check if field should be indexed."""
        return any(c.name == "index" for c in self.constraints)

    def to_sqlalchemy_column(self) -> str:
        """
        Generate SQLAlchemy column definition string.

        Returns:
            String representation of column definition
        """
        parts = []

        # Type with parameters
        if self.sqlalchemy_type == "String" and self.length:
            parts.append(f"String({self.length})")
        elif self.sqlalchemy_type == "Numeric" and self.precision:
            if self.scale:
                parts.append(f"Numeric({self.precision}, {self.scale})")
            else:
                parts.append(f"Numeric({self.precision})")
        elif self.sqlalchemy_type in ["EmailType", "PhoneNumberType", "MoneyType"]:
            parts.append(self.sqlalchemy_type + "()")
        else:
            parts.append(self.sqlalchemy_type + "()")

        # Foreign key
        if self.is_foreign_key and self.foreign_table:
            parts.append(f"ForeignKey('{self.foreign_table}.id')")

        # Constraints
        constraint_parts = []
        if self.is_unique:
            constraint_parts.append("unique=True")
        if self.is_nullable:
            constraint_parts.append("nullable=True")
        else:
            constraint_parts.append("nullable=False")
        if self.is_indexed:
            constraint_parts.append("index=True")

        if constraint_parts:
            parts.append(", ".join(constraint_parts))

        return ", ".join(parts)


class FieldParser:
    """
    Parser for field definitions from CLI arguments.

    Parses field definitions in the format:
    - "name:type" - Basic field
    - "name:type:constraint" - Field with single constraint
    - "name:type:constraint1,constraint2" - Field with multiple constraints

    Examples:
        "name:str" -> String field named "name"
        "email:str:unique" -> Unique string field named "email"
        "age:int:nullable" -> Nullable integer field named "age"
        "price:decimal:nullable,index" -> Nullable, indexed decimal field
        "user_id:int:fk:users" -> Foreign key to users table
    """

    def __init__(self):
        """Initialize the field parser."""
        pass

    def parse_fields(self, fields_str: Optional[str]) -> List[FieldDefinition]:
        """
        Parse a comma-separated string of field definitions.

        Args:
            fields_str: Comma-separated field definitions

        Returns:
            List of FieldDefinition objects

        Raises:
            ValueError: If field definition is invalid
        """
        if not fields_str:
            return []

        # Split by comma (but not inside parentheses)
        field_defs = []
        current = []
        paren_depth = 0

        for char in fields_str:
            if char == "(":
                paren_depth += 1
                current.append(char)
            elif char == ")":
                paren_depth -= 1
                current.append(char)
            elif char == "," and paren_depth == 0:
                field_defs.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            field_defs.append("".join(current).strip())

        # Parse each field definition
        fields = []
        for field_def in field_defs:
            if field_def:
                fields.append(self.parse_field(field_def))

        return fields

    def parse_field(self, field_str: str) -> FieldDefinition:
        """
        Parse a single field definition.

        Args:
            field_str: Field definition string

        Returns:
            FieldDefinition object

        Raises:
            ValueError: If field definition is invalid
        """
        parts = field_str.split(":")

        if len(parts) < 2:
            raise ValueError(
                f"Invalid field definition: {field_str}. Expected format: name:type[:constraints]"
            )

        name = parts[0].strip()
        type_str = parts[1].strip().lower()
        constraint_strs = parts[2:] if len(parts) > 2 else []

        # Validate field name
        if not name.isidentifier():
            raise ValueError(
                f"Invalid field name: {name}. Must be a valid Python identifier."
            )

        # Map type
        if type_str not in TYPE_MAPPING:
            raise ValueError(
                f"Unsupported field type: {type_str}. "
                f"Supported types: {', '.join(TYPE_MAPPING.keys())}"
            )

        sqlalchemy_type_raw = TYPE_MAPPING[type_str]

        # Handle custom types
        if isinstance(sqlalchemy_type_raw, str):
            sqlalchemy_type = sqlalchemy_type_raw
            python_type = "str"  # Custom types are strings
        else:
            sqlalchemy_type = getattr(sqlalchemy_type_raw, "__name__", str(sqlalchemy_type_raw))
            python_type = self._get_python_type(sqlalchemy_type)

        # Parse constraints
        constraints = []
        is_foreign_key = False
        foreign_table = None

        for constraint_str in constraint_strs:
            constraint_str = constraint_str.strip()

            # Handle foreign key: fk:table_name or fk(table_name)
            if constraint_str.startswith("fk"):
                is_foreign_key = True
                # Try to extract table name
                if "(" in constraint_str:
                    # Format: fk(users)
                    table_start = constraint_str.index("(") + 1
                    table_end = constraint_str.index(")")
                    foreign_table = constraint_str[table_start:table_end].strip()
                elif len(constraint_strs) > constraint_strs.index(constraint_str) + 1:
                    # Format: fk:users (next part is table name)
                    idx = constraint_strs.index(constraint_str)
                    foreign_table = constraint_strs[idx + 1].strip()
                    constraint_strs.pop(idx + 1)  # Remove table name from constraints
                else:
                    # Infer from field name (e.g., user_id -> users)
                    if name.endswith("_id"):
                        foreign_table = name[:-3] + "s"
                    else:
                        raise ValueError(
                            f"Cannot infer foreign table for field {name}. "
                            "Specify as fk:table_name or fk(table_name)"
                        )
                constraints.append(FieldConstraint("foreign_key", foreign_table))

            # Handle other constraints
            elif constraint_str in ["unique", "nullable", "index"]:
                constraints.append(FieldConstraint(constraint_str))

            else:
                # Try to parse as key=value
                if "=" in constraint_str:
                    key, value = constraint_str.split("=", 1)
                    constraints.append(FieldConstraint(key.strip(), value.strip()))
                else:
                    # Unknown constraint, add as-is
                    constraints.append(FieldConstraint(constraint_str))

        # Determine type-specific parameters
        length = None
        precision = None
        scale = None

        if sqlalchemy_type == "String":
            length = DEFAULT_STRING_LENGTH
        elif sqlalchemy_type == "Numeric":
            if type_str in ["money", "decimal"]:
                precision = 15
                scale = 2
            else:
                precision = 10
                scale = 2

        return FieldDefinition(
            name=name,
            type=type_str,
            sqlalchemy_type=sqlalchemy_type,
            python_type=python_type,
            constraints=constraints,
            is_foreign_key=is_foreign_key,
            foreign_table=foreign_table,
            length=length,
            precision=precision,
            scale=scale,
        )

    def _get_python_type(self, sqlalchemy_type: str) -> str:
        """
        Map SQLAlchemy type to Python type hint.

        Args:
            sqlalchemy_type: SQLAlchemy type name

        Returns:
            Python type hint string
        """
        type_map = {
            "String": "str",
            "Text": "str",
            "Integer": "int",
            "Float": "float",
            "Numeric": "Decimal",
            "Boolean": "bool",
            "Date": "date",
            "DateTime": "datetime",
        }
        return type_map.get(sqlalchemy_type, "Any")

    def validate_fields(self, fields: List[FieldDefinition]) -> List[str]:
        """
        Validate a list of field definitions.

        Args:
            fields: List of field definitions to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        field_names = set()

        for field in fields:
            # Check for duplicate names
            if field.name in field_names:
                errors.append(f"Duplicate field name: {field.name}")
            field_names.add(field.name)

            # Check for reserved names
            reserved = [
                "id",
                "created_at",
                "updated_at",
                "is_deleted",
                "deleted_at",
                "created_by_id",
                "updated_by_id",
            ]
            if field.name in reserved:
                errors.append(
                    f"Field name '{field.name}' is reserved. "
                    f"Reserved names: {', '.join(reserved)}"
                )

            # Validate foreign key has table
            if field.is_foreign_key and not field.foreign_table:
                errors.append(
                    f"Foreign key field '{field.name}' missing table reference"
                )

        return errors


def parse_field_definitions(fields_str: Optional[str]) -> List[FieldDefinition]:
    """
    Convenience function to parse field definitions.

    Args:
        fields_str: Comma-separated field definitions

    Returns:
        List of FieldDefinition objects

    Raises:
        ValueError: If field definitions are invalid
    """
    parser = FieldParser()
    fields = parser.parse_fields(fields_str)

    # Validate
    errors = parser.validate_fields(fields)
    if errors:
        raise ValueError(
            "Invalid field definitions:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return fields
