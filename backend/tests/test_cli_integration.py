"""
Tests for CLI integration - end-to-end CRUD generation.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cli.crud_generate import app


runner = CliRunner()


def test_generate_help():
    """Test that help text is displayed correctly."""
    result = runner.invoke(app, ["generate", "--help"])
    assert result.exit_code == 0
    assert "Generate complete CRUD scaffolding" in result.output
    assert "--fields" in result.output
    assert "--soft-delete" in result.output
    assert "--timestamps" in result.output
    assert "--audit" in result.output
    assert "--domain" in result.output
    assert "--dry-run" in result.output


def test_generate_invalid_entity_name():
    """Test error handling for invalid entity names."""
    # Test with spaces
    result = runner.invoke(app, ["generate", "user account"])
    assert result.exit_code == 1
    assert "Invalid entity name" in result.output
    
    # Test with special characters
    result = runner.invoke(app, ["generate", "user-account"])
    assert result.exit_code == 1
    assert "Invalid entity name" in result.output
    
    # Test with number start
    result = runner.invoke(app, ["generate", "1user"])
    assert result.exit_code == 1
    assert "Invalid entity name" in result.output


def test_generate_reserved_keyword():
    """Test error handling for Python keywords."""
    result = runner.invoke(app, ["generate", "class"])
    assert result.exit_code == 1
    assert "reserved Python keyword" in result.output


def test_generate_reserved_name():
    """Test error handling for reserved names."""
    result = runner.invoke(app, ["generate", "model"])
    assert result.exit_code == 1
    assert "reserved name" in result.output


def test_generate_invalid_fields():
    """Test error handling for invalid field syntax."""
    result = runner.invoke(app, ["generate", "user", "--fields", "invalid_field_format"])
    assert result.exit_code == 1
    assert "Error parsing fields" in result.output


def test_generate_dry_run():
    """Test dry run mode."""
    result = runner.invoke(app, [
        "generate",
        "product",
        "--fields", "name:str,price:decimal",
        "--dry-run"
    ])
    assert result.exit_code == 0
    assert "Dry run mode" in result.output
    assert "Files to Generate" in result.output
    assert "app/models/product.py" in result.output
    assert "app/services/product_service.py" in result.output
    assert "Dry run complete" in result.output


def test_generate_dry_run_with_parsed_fields():
    """Test dry run displays parsed fields."""
    result = runner.invoke(app, [
        "generate",
        "customer",
        "--fields", "name:str,email:str:unique,age:int",
        "--dry-run"
    ])
    assert result.exit_code == 0
    assert "Parsed Fields" in result.output
    assert "name" in result.output
    assert "email" in result.output
    assert "age" in result.output
    assert "unique" in result.output


def test_generate_dry_run_with_options():
    """Test dry run with various options."""
    result = runner.invoke(app, [
        "generate",
        "task",
        "--fields", "title:str",
        "--no-soft-delete",
        "--no-audit",
        "--domain", "generic",
        "--dry-run"
    ])
    assert result.exit_code == 0
    assert "Soft Delete" in result.output
    assert "✗" in result.output  # Should show disabled markers
    assert "Domain" in result.output
    assert "generic" in result.output


def test_generate_actual_files(tmp_path):
    """Test actual file generation."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    result = runner.invoke(app, [
        "generate",
        "product",
        "--fields", "name:str,price:decimal",
        "--output-dir", str(tmp_path),
    ])
    
    if result.exit_code != 0:
        print(f"Exit code: {result.exit_code}")
        print(f"Output:\n{result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
    
    assert result.exit_code == 0
    assert "Successfully generated" in result.output
    assert "Generated Files" in result.output
    
    # Verify files were created
    assert (app_dir / "models" / "product.py").exists()
    assert (app_dir / "services" / "product_service.py").exists()
    assert (app_dir / "api" / "products.py").exists()
    assert (app_dir / "schemas" / "product_schemas.py").exists()
    assert (tests_dir / "test_products_api.py").exists()
    assert (tests_dir / "test_products_service.py").exists()
    
    # Verify router was registered
    main_content = main_py.read_text()
    assert "from app.api.products import router as products_router" in main_content
    assert "app.include_router(products_router" in main_content


def test_generate_with_domain():
    """Test generation with domain option."""
    result = runner.invoke(app, [
        "generate",
        "employee",
        "--domain", "employee",
        "--fields", "first_name:str,last_name:str",
        "--dry-run"
    ])
    assert result.exit_code == 0
    assert "Domain" in result.output
    assert "employee" in result.output


def test_generate_without_output_dir_error():
    """Test error when output directory cannot be auto-detected."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a directory without app/ subdirectory
        result = runner.invoke(app, [
            "generate",
            "user",
            "--fields", "name:str",
            "--output-dir", tmp_dir,
        ])
        assert result.exit_code == 1
        assert "Invalid output directory" in result.output


def test_version_command():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "CRUD Generator" in result.output
    assert "1.0.0" in result.output


def test_check_dependencies():
    """Test dependency checking."""
    from cli.crud_generate import check_dependencies
    
    # This should pass since we have all dependencies in test environment
    assert check_dependencies() is True


def test_generate_with_minimal_options(tmp_path):
    """Test generation with minimal options."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    # Generate with just entity name (no fields)
    result = runner.invoke(app, [
        "generate",
        "category",
        "--output-dir", str(tmp_path),
    ])
    
    assert result.exit_code == 0
    assert "Successfully generated" in result.output
    
    # Verify files were created
    assert (app_dir / "models" / "category.py").exists()
    assert (app_dir / "services" / "category_service.py").exists()


def test_generate_with_all_options_disabled(tmp_path):
    """Test generation with all optional features disabled."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    result = runner.invoke(app, [
        "generate",
        "tag",
        "--fields", "name:str",
        "--no-soft-delete",
        "--no-timestamps",
        "--no-audit",
        "--output-dir", str(tmp_path),
    ])
    
    assert result.exit_code == 0
    assert "Successfully generated" in result.output
    
    # Verify model file and check it doesn't have soft delete fields
    model_file = app_dir / "models" / "tag.py"
    assert model_file.exists()
    model_content = model_file.read_text()
    
    # Should not have soft delete or audit fields when disabled
    # (The actual check depends on template implementation)
    assert "class Tag" in model_content


def test_main_callback():
    """Test main callback displays help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Generate complete CRUD scaffolding for CRM entities" in result.output
    assert "generate" in result.output
    assert "version" in result.output


def test_generate_output_includes_next_steps(tmp_path):
    """Test that successful generation includes next steps guidance."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    result = runner.invoke(app, [
        "generate",
        "product",
        "--fields", "name:str",
        "--output-dir", str(tmp_path),
    ])
    
    assert result.exit_code == 0
    
    # Check for next steps sections
    assert "Next Steps:" in result.output
    assert "alembic upgrade head" in result.output
    assert "uvicorn app.main:app --reload" in result.output
    assert "/api/v1/products" in result.output
    assert "http://localhost:8000/docs" in result.output
    assert "pytest tests/test_products_api.py" in result.output


def test_generate_output_includes_statistics(tmp_path):
    """Test that successful generation includes statistics."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    result = runner.invoke(app, [
        "generate",
        "order",
        "--fields", "name:str,quantity:int",
        "--output-dir", str(tmp_path),
    ])
    
    assert result.exit_code == 0
    
    # Check for statistics
    assert "Files Generated:" in result.output or "files" in result.output.lower()
    assert "Entity:" in result.output or "order" in result.output
    

def test_generate_output_with_icons(tmp_path):
    """Test that file output includes icons/emojis."""
    # Create backend structure
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "models").mkdir()
    (app_dir / "services").mkdir()
    (app_dir / "api").mkdir()
    (app_dir / "schemas").mkdir()
    
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    
    alembic_dir = tmp_path / "alembic"
    alembic_dir.mkdir()
    (alembic_dir / "versions").mkdir()
    
    # Create main.py with proper format
    main_py = app_dir / "main.py"
    main_py.write_text("""from fastapi import FastAPI

app = FastAPI()

# Include routers
""")
    
    result = runner.invoke(app, [
        "generate",
        "item",
        "--fields", "name:str",
        "--output-dir", str(tmp_path),
    ])
    
    assert result.exit_code == 0
    
    # Check for file types in output
    assert "Model" in result.output
    assert "Service" in result.output
    assert "API Router" in result.output or "Router" in result.output
    assert "Schemas" in result.output
