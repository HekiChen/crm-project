"""
Tests for statistics API endpoints.
"""
import pytest
from datetime import datetime, timedelta, date

from app.models.employee import Employee
from app.models.department import Department
from app.models.role import Role
from app.models.work_log import WorkLog


@pytest.mark.asyncio
async def test_get_dashboard_stats_requires_auth(client):
    """Test that dashboard stats endpoint requires authentication."""
    response = await client.get("/api/v1/stats/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_dashboard_stats_success(client, db_session):
    """Test getting dashboard statistics with valid data."""
    # Create test data - 3 employees
    for i in range(3):
        employee = Employee(
            first_name=f"Test{i}",
            last_name=f"Employee{i}",
            email=f"test{i}@example.com",
            employee_number=f"EMP{i:03d}",
            hire_date=date.today(),
            is_deleted=False
        )
        db_session.add(employee)
    
    # Create test data - 2 departments
    for i in range(2):
        dept = Department(
            code=f"DEPT{i:02d}",
            name=f"Test Department {i}",
            is_deleted=False
        )
        db_session.add(dept)
    
    # Create test data - 4 roles
    for i in range(4):
        role = Role(
            code=f"ROLE{i:02d}",
            name=f"Test Role {i}",
            is_deleted=False
        )
        db_session.add(role)
    
    await db_session.commit()
    
    # Fetch first employee for work logs
    from sqlalchemy import select
    result = await db_session.execute(select(Employee).limit(1))
    employee = result.scalar_one()
    
    # Create work logs - 5 recent (last 7 days), 2 old (> 7 days)
    today = datetime.utcnow().date()
    
    # Recent work logs (should be counted)
    for i in range(5):
        work_log = WorkLog(
            employee_id=employee.id,
            date=today - timedelta(days=i),
            hours=8.0,
            description=f"Recent work {i}"
        )
        db_session.add(work_log)
    
    # Old work logs (should NOT be counted - more than 7 days ago)
    for i in range(2):
        work_log = WorkLog(
            employee_id=employee.id,
            date=today - timedelta(days=8 + i),
            hours=8.0,
            description=f"Old work {i}"
        )
        db_session.add(work_log)
    
    await db_session.commit()
    
    # Mock authentication by bypassing get_current_employee
    from app.models.employee import Employee as EmployeeModel
    from app.dependencies.auth import get_current_employee
    
    async def mock_get_current_employee():
        return employee
    
    from app.main import app
    app.dependency_overrides[get_current_employee] = mock_get_current_employee
    
    # Test the endpoint
    response = await client.get("/api/v1/stats/dashboard")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_json = response.json()
    
    # Response is wrapped in {data: {...}, meta: {...}}
    assert "data" in response_json
    data = response_json["data"]
    
    # Verify counts
    assert data["total_employees"] == 3
    assert data["total_departments"] == 2
    assert data["total_roles"] == 4
    assert data["recent_activities"] == 5  # Only last 7 days


@pytest.mark.asyncio
async def test_get_dashboard_stats_excludes_deleted(client, db_session):
    """Test that deleted records are excluded from statistics."""
    # Create active records
    active_emp = Employee(
        first_name="Active",
        last_name="Employee",
        email="active@example.com",
        employee_number="EMP001",
        hire_date=date.today(),
        is_deleted=False
    )
    db_session.add(active_emp)
    
    # Create deleted records (should not be counted)
    deleted_emp = Employee(
        first_name="Deleted",
        last_name="Employee",
        email="deleted@example.com",
        employee_number="EMP002",
        hire_date=date.today(),
        is_deleted=True
    )
    db_session.add(deleted_emp)
    
    deleted_dept = Department(
        code="DEPT001",
        name="Deleted Department",
        is_deleted=True
    )
    db_session.add(deleted_dept)
    
    deleted_role = Role(
        code="ROLE001",
        name="Deleted Role",
        is_deleted=True
    )
    db_session.add(deleted_role)
    
    await db_session.commit()
    
    # Mock authentication
    from app.dependencies.auth import get_current_employee
    
    async def mock_get_current_employee():
        return active_emp
    
    from app.main import app
    app.dependency_overrides[get_current_employee] = mock_get_current_employee
    
    # Test the endpoint
    response = await client.get("/api/v1/stats/dashboard")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json
    data = response_json["data"]
    
    # Verify only active records are counted
    assert data["total_employees"] == 1
    assert data["total_departments"] == 0
    assert data["total_roles"] == 0
    assert data["recent_activities"] == 0


@pytest.mark.asyncio
async def test_get_dashboard_stats_empty_database(client, db_session):
    """Test dashboard stats with empty database."""
    # Create one employee for authentication
    employee = Employee(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        employee_number="EMP001",
        hire_date=date.today(),
        is_deleted=False
    )
    db_session.add(employee)
    await db_session.commit()
    
    # Mock authentication
    from app.dependencies.auth import get_current_employee
    
    async def mock_get_current_employee():
        return employee
    
    from app.main import app
    app.dependency_overrides[get_current_employee] = mock_get_current_employee
    
    # Test the endpoint
    response = await client.get("/api/v1/stats/dashboard")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json
    data = response_json["data"]
    
    # Verify all counts are at least 1 (auth employee) or 0
    assert data["total_employees"] >= 1  # At least the auth employee
    assert data["total_departments"] == 0
    assert data["total_roles"] == 0
    assert data["recent_activities"] == 0


@pytest.mark.asyncio
async def test_get_dashboard_stats_seven_day_boundary(client, db_session):
    """Test that work logs exactly 7 days old are included."""
    # Create employee
    employee = Employee(
        first_name="Test",
        last_name="Employee",
        email="test@example.com",
        employee_number="EMP001",
        hire_date=date.today(),
        is_deleted=False
    )
    db_session.add(employee)
    await db_session.commit()
    
    today = datetime.utcnow().date()
    
    # Create work log exactly 7 days ago (should be included)
    work_log_boundary = WorkLog(
        employee_id=employee.id,
        date=today - timedelta(days=7),
        hours=8.0,
        description="Boundary work log"
    )
    db_session.add(work_log_boundary)
    
    # Create work log 8 days ago (should NOT be included)
    work_log_old = WorkLog(
        employee_id=employee.id,
        date=today - timedelta(days=8),
        hours=8.0,
        description="Old work log"
    )
    db_session.add(work_log_old)
    
    await db_session.commit()
    
    # Mock authentication
    from app.dependencies.auth import get_current_employee
    
    async def mock_get_current_employee():
        return employee
    
    from app.main import app
    app.dependency_overrides[get_current_employee] = mock_get_current_employee
    
    # Test the endpoint
    response = await client.get("/api/v1/stats/dashboard")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json
    data = response_json["data"]
    
    # Verify only the 7-day boundary work log is counted
    assert data["recent_activities"] == 1


@pytest.mark.asyncio
async def test_get_dashboard_stats_response_structure(client, db_session):
    """Test that response has correct structure and types."""
    # Create minimal test data
    employee = Employee(
        first_name="Test",
        last_name="Employee",
        email="test@example.com",
        employee_number="EMP001",
        hire_date=date.today(),
        is_deleted=False
    )
    db_session.add(employee)
    await db_session.commit()
    
    # Mock authentication
    from app.dependencies.auth import get_current_employee
    
    async def mock_get_current_employee():
        return employee
    
    from app.main import app
    app.dependency_overrides[get_current_employee] = mock_get_current_employee
    
    # Test the endpoint
    response = await client.get("/api/v1/stats/dashboard")
    
    # Clean up override
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json
    data = response_json["data"]
    
    # Verify structure
    assert "total_employees" in data
    assert "total_departments" in data
    assert "total_roles" in data
    assert "recent_activities" in data
    
    # Verify types (all should be integers)
    assert isinstance(data["total_employees"], int)
    assert isinstance(data["total_departments"], int)
    assert isinstance(data["total_roles"], int)
    assert isinstance(data["recent_activities"], int)
    
    # Verify non-negative values
    assert data["total_employees"] >= 0
    assert data["total_departments"] >= 0
    assert data["total_roles"] >= 0
    assert data["recent_activities"] >= 0
