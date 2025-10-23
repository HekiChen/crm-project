"""
Template validation test.

Tests that all Jinja2 templates can be rendered with sample data.
"""
import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

from cli.field_parser import FieldDefinition, FieldConstraint


@pytest.fixture
def template_env():
    """Create Jinja2 environment."""
    template_dir = Path(__file__).parent.parent / "templates" / "crud"
    return Environment(loader=FileSystemLoader(str(template_dir)))


@pytest.fixture
def sample_context():
    """Create sample template context."""
    return {
        "entity_name": "user",
        "entity_class": "User",
        "table_name": "users",
        "endpoint_prefix": "users",
        "description": "User entity for authentication and authorization",
        "use_custom_types": False,
        "domain_mixins": [],
        "soft_delete": True,
        "audit": True,
        "timestamps": True,
        "fields": [
            FieldDefinition(
                name="username",
                type="str",
                sqlalchemy_type="String",
                python_type="str",
                constraints=[FieldConstraint("unique")],
                length=100,
            ),
            FieldDefinition(
                name="email",
                type="str",
                sqlalchemy_type="String",
                python_type="str",
                constraints=[FieldConstraint("unique")],
                length=255,
            ),
            FieldDefinition(
                name="age",
                type="int",
                sqlalchemy_type="Integer",
                python_type="int",
                constraints=[FieldConstraint("nullable")],
            ),
        ],
        "repr_fields": "username='{self.username}'",
        "relationships": [],
        "has_validators": True,
        "validation_tests": True,
        "migration_message": "Create user table",
        "revision_id": "abc123",
        "down_revision": "'previous_revision'",
        "create_date": datetime.utcnow().isoformat(),
        "foreign_keys": [],
        "unique_constraints": ["username", "email"],
        "indexed_fields": [],
    }


def test_model_template_renders(template_env, sample_context):
    """Test that model template renders without errors."""
    template = template_env.get_template("model.py.jinja2")
    
    # Add sample values for test rendering
    for field in sample_context["fields"]:
        field.doc = f"The {field.name} field"
    
    result = template.render(**sample_context)
    
    assert "class User(BaseModel)" in result
    assert "username: Mapped[str]" in result
    assert "email: Mapped[str]" in result
    assert "age: Mapped[Optional[int]]" in result
    assert "__tablename__ = \"users\"" in result


def test_service_template_renders(template_env, sample_context):
    """Test that service template renders without errors."""
    template = template_env.get_template("service.py.jinja2")
    result = template.render(**sample_context)
    
    assert "class UserService(BaseService" in result
    assert "from app.models.user import User" in result
    assert "from app.schemas.user_schemas import UserCreate, UserUpdate" in result


def test_schemas_template_renders(template_env, sample_context):
    """Test that schemas template renders without errors."""
    template = template_env.get_template("schemas.py.jinja2")
    
    # Add sample values
    for field in sample_context["fields"]:
        field.doc = f"The {field.name} field"
    
    result = template.render(**sample_context)
    
    assert "class UserCreate(CreateSchema)" in result
    assert "class UserUpdate(UpdateSchema)" in result
    assert "class UserResponse(ResponseSchema)" in result
    assert "class UserListResponse(ListResponseSchema[UserResponse])" in result


def test_api_template_renders(template_env, sample_context):
    """Test that API template renders without errors."""
    template = template_env.get_template("api.py.jinja2")
    result = template.render(**sample_context)
    
    assert "router = APIRouter(" in result
    assert 'prefix="/users"' in result
    assert "async def create_user(" in result
    assert "async def get_user(" in result
    assert "async def list_users(" in result
    assert "async def update_user(" in result
    assert "async def delete_user(" in result


def test_test_api_template_renders(template_env, sample_context):
    """Test that API test template renders without errors."""
    template = template_env.get_template("test_api.py.jinja2")
    
    # Add sample values for tests
    for field in sample_context["fields"]:
        field.sample_value = f'"{field.name}_value"' if field.python_type == "str" else "123"
        field.sample_value_pattern = f'f"{{field.name}}_{{i}}"' if field.python_type == "str" else "i"
        field.updated_sample_value = f'"{field.name}_updated"' if field.python_type == "str" else "456"
    
    result = template.render(**sample_context)
    
    assert "class TestUserAPI:" in result
    assert "async def test_create_user(" in result
    assert "async def test_get_user_by_id(" in result
    assert "async def test_list_users(" in result
    assert "async def test_update_user(" in result
    assert "async def test_delete_user(" in result


def test_test_service_template_renders(template_env, sample_context):
    """Test that service test template renders without errors."""
    template = template_env.get_template("test_service.py.jinja2")
    
    # Add sample values for tests
    for field in sample_context["fields"]:
        field.sample_value = f'"{field.name}_value"' if field.python_type == "str" else "123"
        field.sample_value_pattern = f'f"{{field.name}}_{{i}}"' if field.python_type == "str" else "i"
        field.updated_sample_value = f'"{field.name}_updated"' if field.python_type == "str" else "456"
    
    result = template.render(**sample_context)
    
    assert "class TestUserService:" in result
    assert "async def test_create_user(" in result
    assert "async def test_get_by_id(" in result
    assert "async def test_get_list(" in result
    assert "async def test_update_user(" in result
    assert "async def test_delete_user(" in result


def test_migration_template_renders(template_env, sample_context):
    """Test that migration template renders without errors."""
    template = template_env.get_template("migration.py.jinja2")
    result = template.render(**sample_context)
    
    assert "revision = 'abc123'" in result
    assert "def upgrade() -> None:" in result
    assert "def downgrade() -> None:" in result
    assert "op.create_table(" in result
    assert "'users'" in result
    assert "op.drop_table('users')" in result


def test_all_templates_exist():
    """Test that all expected templates exist."""
    template_dir = Path(__file__).parent.parent / "templates" / "crud"
    
    expected_templates = [
        "model.py.jinja2",
        "service.py.jinja2",
        "schemas.py.jinja2",
        "api.py.jinja2",
        "test_api.py.jinja2",
        "test_service.py.jinja2",
        "migration.py.jinja2",
    ]
    
    for template_name in expected_templates:
        template_path = template_dir / template_name
        assert template_path.exists(), f"Template {template_name} not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
