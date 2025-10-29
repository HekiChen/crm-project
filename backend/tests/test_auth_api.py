"""
Tests for authentication API endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from uuid import uuid4

from app.models.employee import Employee
from app.models.role import Role
from app.models.employee_role import EmployeeRole
from app.utils.auth import hash_password


@pytest_asyncio.fixture
async def test_employee(db_session: AsyncSession):
    """Create a test employee with password."""
    employee = Employee(
        id=uuid4(),
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        employee_number="EMP001",
        hire_date=date(2023, 1, 1),
        password_hash=hash_password("password123"),
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    return employee


@pytest_asyncio.fixture
async def test_employee_without_password(db_session: AsyncSession):
    """Create a test employee without password (NULL password_hash)."""
    employee = Employee(
        id=uuid4(),
        email="nopassword@example.com",
        first_name="No",
        last_name="Password",
        employee_number="EMP002",
        hire_date=date(2023, 1, 1),
        password_hash=None,  # No password set
        is_active=True
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    return employee


@pytest_asyncio.fixture
async def test_inactive_employee(db_session: AsyncSession):
    """Create an inactive employee."""
    employee = Employee(
        id=uuid4(),
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        employee_number="EMP003",
        hire_date=date(2023, 1, 1),
        password_hash=hash_password("password123"),
        is_active=False
    )
    db_session.add(employee)
    await db_session.commit()
    await db_session.refresh(employee)
    return employee


@pytest_asyncio.fixture
async def test_employee_with_roles(db_session: AsyncSession):
    """Create a test employee with assigned roles."""
    # Create employee
    employee = Employee(
        id=uuid4(),
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        employee_number="EMP004",
        hire_date=date(2023, 1, 1),
        password_hash=hash_password("admin123"),
        is_active=True
    )
    db_session.add(employee)
    
    # Create roles
    role1 = Role(
        id=uuid4(),
        name="Administrator",
        code="ADMIN",
        description="System administrator",
        is_system_role=True
    )
    role2 = Role(
        id=uuid4(),
        name="Manager",
        code="MANAGER",
        description="Department manager",
        is_system_role=False
    )
    db_session.add(role1)
    db_session.add(role2)
    
    await db_session.commit()
    await db_session.refresh(employee)
    await db_session.refresh(role1)
    await db_session.refresh(role2)
    
    # Assign roles to employee
    employee_role1 = EmployeeRole(
        id=uuid4(),
        employee_id=employee.id,
        role_id=role1.id
    )
    employee_role2 = EmployeeRole(
        id=uuid4(),
        employee_id=employee.id,
        role_id=role2.id
    )
    db_session.add(employee_role1)
    db_session.add(employee_role2)
    
    await db_session.commit()
    return employee


@pytest.mark.asyncio
class TestLoginEndpoint:
    """Tests for /auth/login endpoint."""
    
    async def test_login_with_valid_credentials(self, client: AsyncClient, test_employee):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800  # 30 minutes in seconds
    
    async def test_login_with_invalid_email(self, client: AsyncClient, test_employee):
        """Test login with non-existent email returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        json_data = response.json()
        # Check if detail is in root or error key
        error_detail = json_data.get("detail") or json_data.get("error", {}).get("message", "")
        assert "Invalid credentials" in error_detail or "Invalid credentials" in str(json_data)
    
    async def test_login_with_invalid_password(self, client: AsyncClient, test_employee):
        """Test login with wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        json_data = response.json()
        error_detail = json_data.get("detail") or json_data.get("error", {}).get("message", "")
        assert "Invalid credentials" in error_detail or "Invalid credentials" in str(json_data)
    
    async def test_login_with_null_password_hash(self, client: AsyncClient, test_employee_without_password):
        """Test login with employee that has no password set returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nopassword@example.com",
                "password": "anypassword"
            }
        )
        
        assert response.status_code == 401
        json_data = response.json()
        error_detail = json_data.get("detail") or json_data.get("error", {}).get("message", "")
        assert "Invalid credentials" in error_detail or "Invalid credentials" in str(json_data)
    
    async def test_login_with_inactive_account(self, client: AsyncClient, test_inactive_employee):
        """Test login with inactive account returns 403."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "inactive@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 403
        json_data = response.json()
        error_detail = json_data.get("detail") or json_data.get("error", {}).get("message", "")
        assert "inactive" in error_detail.lower() or "inactive" in str(json_data).lower()


@pytest.mark.asyncio
class TestRefreshEndpoint:
    """Tests for /auth/refresh endpoint."""
    
    async def test_refresh_with_valid_refresh_token(self, client: AsyncClient, test_employee):
        """Test refreshing access token with valid refresh token."""
        # First login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser@example.com",
                "password": "password123"
            }
        )
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # Use refresh token to get new access token
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
    
    async def test_refresh_with_access_token_fails(self, client: AsyncClient, test_employee):
        """Test that using access token for refresh fails."""
        # Login to get tokens
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser@example.com",
                "password": "password123"
            }
        )
        access_token = login_response.json()["data"]["access_token"]
        
        # Try to use access token for refresh (should fail)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}
        )
        
        assert response.status_code == 401
        json_data = response.json()
        error_detail = json_data.get("detail") or json_data.get("error", {}).get("message", "")
        assert "Invalid token type" in error_detail or "Invalid token type" in str(json_data)
    
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """Test refresh with invalid token returns 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestMeEndpoint:
    """Tests for /auth/me endpoint."""
    
    async def test_get_current_user_with_valid_token(self, client: AsyncClient, test_employee):
        """Test getting current user info with valid token."""
        # Login first
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser@example.com",
                "password": "password123"
            }
        )
        access_token = login_response.json()["data"]["access_token"]
        
        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "testuser@example.com"
        assert data["first_name"] == "Test"
        assert data["last_name"] == "User"
        assert data["employee_number"] == "EMP001"
        assert data["is_active"] is True
        assert "roles" in data
        assert isinstance(data["roles"], list)
    
    async def test_get_current_user_with_roles(self, client: AsyncClient, test_employee_with_roles):
        """Test that /me endpoint returns employee roles."""
        # Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin@example.com",
                "password": "admin123"
            }
        )
        access_token = login_response.json()["data"]["access_token"]
        
        # Get current user
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["roles"]) == 2
        
        role_codes = [role["code"] for role in data["roles"]]
        assert "ADMIN" in role_codes
        assert "MANAGER" in role_codes
    
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """Test that accessing /me without token returns 401."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_with_invalid_token(self, client: AsyncClient):
        """Test that accessing /me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestLogoutEndpoint:
    """Tests for /auth/logout endpoint."""
    
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint returns success message."""
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "logged out" in data["message"].lower()
