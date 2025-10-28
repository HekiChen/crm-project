import pytest
from datetime import date
from uuid import uuid4
from fastapi import HTTPException, status
from app.services.employee_service import EmployeeService
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.employee_schemas import EmployeeCreate, EmployeeUpdate

@pytest.mark.asyncio
async def test_employee_create_invalid_department(db_session):
    svc = EmployeeService(db_session)
    # Create with non-existent department
    emp_in = EmployeeCreate(
        first_name="A", last_name="B", email="a@b.com", employee_number="E-1", hire_date=date.today(), department_id=uuid4()
    )
    with pytest.raises(HTTPException) as exc:
        await svc.create(emp_in)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Department not found" in exc.value.detail

@pytest.mark.asyncio
async def test_employee_create_valid_department(db_session):
    svc = EmployeeService(db_session)
    # Create department
    dept = Department(code="D1", name="Dept1")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    # Create employee with valid department
    emp_in = EmployeeCreate(
        first_name="A", last_name="B", email="a2@b.com", employee_number="E-2", hire_date=date.today(), department_id=dept.id
    )
    emp = await svc.create(emp_in)
    assert emp.department_id == dept.id

@pytest.mark.asyncio
async def test_employee_update_invalid_department(db_session):
    svc = EmployeeService(db_session)
    # Create department and employee
    dept = Department(code="D2", name="Dept2")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    emp_in = EmployeeCreate(
        first_name="A", last_name="B", email="a3@b.com", employee_number="E-3", hire_date=date.today(), department_id=dept.id
    )
    emp = await svc.create(emp_in)
    # Try to update to non-existent department
    upd = EmployeeUpdate(department_id=uuid4())
    with pytest.raises(HTTPException) as exc:
        await svc.update(emp.id, upd)
    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Department not found" in exc.value.detail
