"""
Tests for FileGenerator class.
"""
import tempfile
from pathlib import Path

import pytest

from cli.field_parser import FieldDefinition, FieldConstraint
from cli.file_generator import FileGenerator


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    return tmp_path / "output"


@pytest.fixture
def template_dir():
    """Get templates directory."""
    current_file = Path(__file__).resolve()
    backend_dir = current_file.parent.parent
    return backend_dir / "templates" / "crud"


@pytest.fixture
def file_generator(template_dir, temp_output_dir):
    """Create file generator instance."""
    return FileGenerator(template_dir=template_dir, output_dir=temp_output_dir)


@pytest.fixture
def sample_fields():
    """Create sample field definitions."""
    return [
        FieldDefinition(
            name="name",
            type="str",
            sqlalchemy_type="String",
            python_type="str",
            constraints=[],
            length=255,
        ),
        FieldDefinition(
            name="email",
            type="email",
            sqlalchemy_type="EmailType",
            python_type="str",
            constraints=[FieldConstraint(name="unique")],
        ),
        FieldDefinition(
            name="age",
            type="int",
            sqlalchemy_type="Integer",
            python_type="int",
            constraints=[FieldConstraint(name="nullable")],
        ),
    ]


def test_to_snake_case(file_generator):
    """Test snake_case conversion."""
    assert file_generator._to_snake_case("UserProfile") == "user_profile"
    assert file_generator._to_snake_case("user") == "user"
    assert file_generator._to_snake_case("APIKey") == "api_key"
    assert file_generator._to_snake_case("XMLParser") == "xml_parser"


def test_to_pascal_case(file_generator):
    """Test PascalCase conversion."""
    assert file_generator._to_pascal_case("user_profile") == "UserProfile"
    assert file_generator._to_pascal_case("user") == "User"
    assert file_generator._to_pascal_case("api_key") == "ApiKey"


def test_pluralize(file_generator):
    """Test word pluralization."""
    assert file_generator._pluralize("user") == "users"
    assert file_generator._pluralize("company") == "companies"
    assert file_generator._pluralize("address") == "addresses"
    assert file_generator._pluralize("church") == "churches"
    assert file_generator._pluralize("dish") == "dishes"


def test_prepare_context(file_generator, sample_fields):
    """Test context preparation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    assert context["entity_name"] == "user"
    assert context["entity_class"] == "User"
    assert context["table_name"] == "users"
    assert context["endpoint_prefix"] == "users"
    assert context["fields"] == sample_fields
    assert context["soft_delete"] is True
    assert context["timestamps"] is True
    assert context["audit"] is True
    assert context["domain_mixins"] == []
    
    # Check sample values were added
    assert sample_fields[0].sample_value == '"name_value"'
    assert sample_fields[1].sample_value == '"email_value"'
    assert sample_fields[2].sample_value == "123"


def test_prepare_context_with_employee_domain(file_generator, sample_fields):
    """Test context preparation with employee domain."""
    context = file_generator._prepare_context(
        entity_name="employee",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain="employee",
    )
    
    assert context["domain_mixins"] == ["PersonMixin", "ContactMixin", "EmployeeMixin"]


def test_prepare_context_with_customer_domain(file_generator, sample_fields):
    """Test context preparation with customer domain."""
    context = file_generator._prepare_context(
        entity_name="customer",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain="customer",
    )
    
    assert context["domain_mixins"] == ["PersonMixin", "ContactMixin", "CustomerMixin"]


def test_render_template(file_generator, sample_fields):
    """Test template rendering."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    # Render model template
    content = file_generator._render_template("model.py.jinja2", context)
    
    assert "class User(BaseModel):" in content
    assert 'name: Mapped[str] = mapped_column(' in content
    assert 'String(255)' in content
    assert "email: Mapped[str] = mapped_column(" in content
    assert "EmailType()" in content
    assert "age: Mapped[Optional[int]] = mapped_column(" in content
    assert "Integer()" in content


def test_generate_model(file_generator, sample_fields):
    """Test model file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_model("user", sample_fields, context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "user.py"
    assert "app/models" in str(file_path)
    
    content = file_path.read_text()
    assert "class User(BaseModel):" in content


def test_generate_service(file_generator, sample_fields):
    """Test service file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_service("user", context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "user_service.py"
    assert "app/services" in str(file_path)
    
    content = file_path.read_text()
    assert "class UserService(BaseService[User, UserCreate, UserUpdate]):" in content


def test_generate_schemas(file_generator, sample_fields):
    """Test schemas file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_schemas("user", context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "user_schemas.py"
    assert "app/schemas" in str(file_path)
    
    content = file_path.read_text()
    assert "class UserCreate(CreateSchema):" in content
    assert "class UserUpdate(UpdateSchema):" in content
    assert "class UserResponse(ResponseSchema):" in content


def test_generate_api(file_generator, sample_fields):
    """Test API router file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_api("users", context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "users.py"
    assert "app/api" in str(file_path)
    
    content = file_path.read_text()
    assert "router = APIRouter(" in content
    assert '@router.post(' in content
    assert 'def create_user' in content


def test_generate_test_api(file_generator, sample_fields):
    """Test API test file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_test_api("users", context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "test_users_api.py"
    assert "tests" in str(file_path)
    
    content = file_path.read_text()
    assert "def test_create_user" in content
    assert "def test_list_users" in content


def test_generate_test_service(file_generator, sample_fields):
    """Test service test file generation."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_test_service("users", context, backup_existing=False)
    
    assert file_path.exists()
    assert file_path.name == "test_users_service.py"
    assert "tests" in str(file_path)
    
    content = file_path.read_text()
    assert "def test_create_user" in content
    assert "class TestUserService:" in content


def test_generate_all(file_generator, sample_fields):
    """Test generating all files."""
    generated_files, migration_path = file_generator.generate_all(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
        backup_existing=False,
        register_router=False,  # Don't register router in tests
        generate_migration=False,  # Don't generate migration in basic test
    )
    
    assert len(generated_files) == 6
    assert migration_path is None
    
    # Check all files were created
    file_names = [f.name for f in generated_files]
    assert "user.py" in file_names
    assert "user_service.py" in file_names
    assert "user_schemas.py" in file_names
    assert "users.py" in file_names
    assert "test_users_api.py" in file_names
    assert "test_users_service.py" in file_names


def test_backup_existing_file(file_generator, sample_fields, temp_output_dir):
    """Test backup of existing files."""
    # Create initial file
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    file_path = file_generator.generate_model("user", sample_fields, context, backup_existing=False)
    original_content = file_path.read_text()
    
    # Modify the file
    file_path.write_text("# Modified content\n" + original_content)
    
    # Generate again with backup
    file_generator.generate_model("user", sample_fields, context, backup_existing=True)
    
    # Check backup was created
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
    assert backup_path.exists()
    
    backup_content = backup_path.read_text()
    assert "# Modified content" in backup_content


def test_file_exists_error(file_generator, sample_fields):
    """Test error when file exists and backup is disabled."""
    context = file_generator._prepare_context(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
    )
    
    # Create initial file
    file_generator.generate_model("user", sample_fields, context, backup_existing=False)
    
    # Try to generate again without backup
    with pytest.raises(FileExistsError):
        file_generator.generate_model("user", sample_fields, context, backup_existing=False)


def test_generate_all_with_router_registration(file_generator, sample_fields, temp_output_dir):
    """Test generating all files with router registration."""
    # Create a mock main.py
    main_py_path = temp_output_dir / "app" / "main.py"
    main_py_path.parent.mkdir(parents=True, exist_ok=True)
    main_py_path.write_text('''"""Main app."""
from fastapi import FastAPI

app = FastAPI()

# Include routers
''')
    
    # Generate with router registration
    generated_files, migration_path = file_generator.generate_all(
        entity_name="user",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
        backup_existing=False,
        register_router=True,
        api_prefix="/api/v1",
        generate_migration=False,
    )
    
    # Check that router was registered
    main_py_content = main_py_path.read_text()
    assert 'from app.api.users import router as users_router' in main_py_content
    assert 'app.include_router(users_router, prefix="/api/v1/users", tags=["users"])' in main_py_content


def test_generate_all_with_migration(file_generator, sample_fields, temp_output_dir):
    """Test generating all files with migration."""
    # Create alembic/versions directory
    versions_dir = temp_output_dir / "alembic" / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate with migration
    generated_files, migration_path = file_generator.generate_all(
        entity_name="product",
        fields=sample_fields,
        soft_delete=True,
        timestamps=True,
        audit=True,
        domain=None,
        backup_existing=False,
        register_router=False,
        generate_migration=True,
    )
    
    # Check migration was generated
    assert migration_path is not None
    assert migration_path.exists()
    assert "create_product_table" in migration_path.name
    assert migration_path.parent == versions_dir
    
    # Check migration content
    migration_content = migration_path.read_text()
    assert "def upgrade()" in migration_content
    assert "def downgrade()" in migration_content
    assert "products" in migration_content

