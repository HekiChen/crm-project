"""
Tests for RouterRegistration class.
"""
import tempfile
from pathlib import Path

import pytest

from cli.router_registration import RouterRegistration


# Sample main.py content
SAMPLE_MAIN_PY = '''"""
FastAPI main application.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.health import router as health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI application instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome"}
'''


@pytest.fixture
def temp_main_py(tmp_path):
    """Create temporary main.py file."""
    main_py = tmp_path / "main.py"
    main_py.write_text(SAMPLE_MAIN_PY)
    return main_py


@pytest.fixture
def router_registration(temp_main_py):
    """Create RouterRegistration instance with temp file."""
    return RouterRegistration(main_py_path=temp_main_py)


def test_load_main_py(router_registration):
    """Test loading main.py content."""
    router_registration.load()
    
    assert router_registration.content
    assert len(router_registration.lines) > 0
    assert 'from fastapi import FastAPI' in router_registration.content


def test_find_import_section_end(router_registration):
    """Test finding end of import section."""
    router_registration.load()
    
    import_end = router_registration._find_import_section_end()
    
    assert import_end > 0
    # Should be after the health_router import
    assert 'import' in router_registration.lines[import_end]


def test_find_router_registration_section(router_registration):
    """Test finding router registration section."""
    router_registration.load()
    
    start_idx, end_idx = router_registration._find_router_registration_section()
    
    assert start_idx > 0
    assert end_idx >= start_idx
    assert '# Include routers' in router_registration.lines[start_idx]


def test_router_import_exists(router_registration):
    """Test checking if router import exists."""
    router_registration.load()
    
    # Health router should exist
    assert router_registration._router_import_exists('health')
    
    # User router should not exist
    assert not router_registration._router_import_exists('users')


def test_router_registration_exists(router_registration):
    """Test checking if router registration exists."""
    router_registration.load()
    
    # Health router should be registered
    assert router_registration._router_registration_exists('health')
    
    # User router should not be registered
    assert not router_registration._router_registration_exists('users')


def test_add_import(router_registration):
    """Test adding router import."""
    router_registration.load()
    
    router_registration._add_import('users')
    
    # Check import was added
    import_statement = "from app.api.users import router as users_router"
    assert any(import_statement in line for line in router_registration.lines)


def test_add_registration(router_registration):
    """Test adding router registration."""
    router_registration.load()
    
    router_registration._add_registration('user', 'users', '/api/v1')
    
    # Check registration was added
    registration = 'app.include_router(users_router, prefix="/api/v1/users", tags=["users"])'
    assert any(registration in line for line in router_registration.lines)


def test_register_router(router_registration, temp_main_py):
    """Test registering a new router."""
    result = router_registration.register_router('user', 'users')
    
    assert result is True
    
    # Check file was updated
    content = temp_main_py.read_text()
    assert 'from app.api.users import router as users_router' in content
    assert 'app.include_router(users_router, prefix="/api/v1/users", tags=["users"])' in content


def test_register_router_skip_if_exists(router_registration):
    """Test skipping registration if already exists."""
    # Register first time
    result1 = router_registration.register_router('user', 'users')
    assert result1 is True
    
    # Try to register again
    result2 = router_registration.register_router('user', 'users', skip_if_exists=True)
    assert result2 is False


def test_register_router_error_if_exists(router_registration):
    """Test error when registering duplicate without skip."""
    # Register first time
    router_registration.register_router('user', 'users')
    
    # Try to register again without skip
    with pytest.raises(ValueError, match="already registered"):
        router_registration.register_router('user', 'users', skip_if_exists=False)


def test_register_multiple_routers(router_registration, temp_main_py):
    """Test registering multiple routers."""
    # Register users router
    router_registration.register_router('user', 'users')
    
    # Register products router
    router_registration.register_router('product', 'products')
    
    # Check both were added
    content = temp_main_py.read_text()
    assert 'from app.api.users import router as users_router' in content
    assert 'from app.api.products import router as products_router' in content
    assert 'app.include_router(users_router' in content
    assert 'app.include_router(products_router' in content


def test_unregister_router(router_registration, temp_main_py):
    """Test unregistering a router."""
    # Register router first
    router_registration.register_router('user', 'users')
    
    # Verify it exists
    content = temp_main_py.read_text()
    assert 'users_router' in content
    
    # Unregister
    result = router_registration.unregister_router('users')
    assert result is True
    
    # Verify it was removed
    content = temp_main_py.read_text()
    assert 'users_router' not in content


def test_unregister_nonexistent_router(router_registration):
    """Test unregistering a router that doesn't exist."""
    result = router_registration.unregister_router('nonexistent')
    assert result is False


def test_list_registered_routers(router_registration):
    """Test listing registered routers."""
    # Initially should have health router
    routers = router_registration.list_registered_routers()
    assert 'health' in routers
    
    # Register users router
    router_registration.register_router('user', 'users')
    
    # Should now have both
    routers = router_registration.list_registered_routers()
    assert 'health' in routers
    assert 'users' in routers


def test_custom_api_prefix(router_registration, temp_main_py):
    """Test registering router with custom API prefix."""
    router_registration.register_router('user', 'users', api_prefix='/api/v2')
    
    content = temp_main_py.read_text()
    assert 'prefix="/api/v2/users"' in content


def test_preserve_formatting(router_registration, temp_main_py):
    """Test that formatting is preserved."""
    # Get original content
    original_lines = temp_main_py.read_text().split('\n')
    
    # Register router
    router_registration.register_router('user', 'users')
    
    # Get new content
    new_lines = temp_main_py.read_text().split('\n')
    
    # Check that original lines still exist (in same order)
    # We should have added lines, not removed or reordered
    assert len(new_lines) > len(original_lines)


def test_file_not_found():
    """Test error when main.py doesn't exist."""
    nonexistent = Path("/tmp/nonexistent_main.py")
    registration = RouterRegistration(main_py_path=nonexistent)
    
    with pytest.raises(FileNotFoundError):
        registration.load()


def test_register_router_with_underscores(router_registration, temp_main_py):
    """Test registering router with underscores in name."""
    router_registration.register_router('work_log', 'work_logs')
    
    content = temp_main_py.read_text()
    assert 'from app.api.work_logs import router as work_logs_router' in content
    assert 'app.include_router(work_logs_router, prefix="/api/v1/work_logs", tags=["work_logs"])' in content
