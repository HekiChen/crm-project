import pytest
from uuid import uuid4
from datetime import date

from fastapi import HTTPException, status

from app.services.department_service import DepartmentService
from app.models.department import Department
from app.models.employee import Employee


@pytest.mark.asyncio
async def test_create_department_success(db_session):
    svc = DepartmentService(db_session)
    data = Department(code="ENG-001", name="Engineering")
    # Use BaseService.create via schema: build a minimal Pydantic-like object
    class In:
        def __init__(self, **kwargs):
            self._d = kwargs

        def model_dump(self, exclude_unset=False):
            return self._d

    created = await svc.create(In(code="ENG-001", name="Engineering"), commit=True)
    assert created.id is not None
    assert created.code == "ENG-001"


@pytest.mark.asyncio
async def test_create_duplicate_code_conflict(db_session):
    svc = DepartmentService(db_session)

    class In:
        def __init__(self, **kwargs):
            self._d = kwargs

        def model_dump(self, exclude_unset=False):
            return self._d

    await svc.create(In(code="SALES-01", name="Sales"))

    with pytest.raises(HTTPException) as exc:
        await svc.create(In(code="SALES-01", name="Sales 2"))

    assert exc.value.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_manager_validation_and_parent_cycle(db_session):
    svc = DepartmentService(db_session)

    class In:
        def __init__(self, **kwargs):
            self._d = kwargs

        def model_dump(self, exclude_unset=False):
            return self._d

    # create an employee to be manager
    emp = Employee(first_name="Joe", last_name="Manager", email="joe.manager@example.com", employee_number="E-1", hire_date=date.today())
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)

    # create parent dept
    parent = await svc.create(In(code="PARENT", name="Parent Dept"))

    # create child with manager and parent
    child = await svc.create(In(code="CHILD", name="Child Dept", manager_id=emp.id, parent_id=parent.id))
    assert child.parent_id == parent.id
    assert child.manager_id == emp.id

    # attempt to set parent to itself via update
    from app.schemas.department_schemas import DepartmentUpdate

    upd = DepartmentUpdate(parent_id=child.id)
    with pytest.raises(HTTPException) as exc2:
        await svc.update(child.id, DepartmentUpdate(parent_id=child.id))
    assert exc2.value.status_code == status.HTTP_400_BAD_REQUEST

    # create a deeper chain and ensure cycle prevention
    a = await svc.create(In(code="A", name="A"))
    b = await svc.create(In(code="B", name="B", parent_id=a.id))

    # updating A.parent to B should create a cycle
    with pytest.raises(HTTPException) as exc3:
        await svc.update(a.id, DepartmentUpdate(parent_id=b.id))
    assert exc3.value.status_code == status.HTTP_400_BAD_REQUEST
