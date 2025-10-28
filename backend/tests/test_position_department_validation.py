import pytest
from uuid import uuid4
from app.services.position_service import PositionService
from app.models.position import Position
from app.models.department import Department
from app.schemas.position_schemas import PositionCreate, PositionUpdate

@pytest.mark.asyncio
async def test_position_create_invalid_department(db_session):
    svc = PositionService(db_session)
    pos_in = PositionCreate(
        name="TestPos", code="TP-1", level=1, department_id=uuid4()
    )
    with pytest.raises(Exception) as exc:
        await svc.create(pos_in)
    assert "Department not found" in str(exc.value)

@pytest.mark.asyncio
async def test_position_create_valid_department(db_session):
    svc = PositionService(db_session)
    dept = Department(code="PD1", name="Dept1")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    pos_in = PositionCreate(
        name="TestPos2", code="TP-2", level=2, department_id=dept.id
    )
    pos = await svc.create(pos_in)
    assert pos.department_id == dept.id

@pytest.mark.asyncio
async def test_position_update_invalid_department(db_session):
    svc = PositionService(db_session)
    dept = Department(code="PD2", name="Dept2")
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    pos_in = PositionCreate(
        name="TestPos3", code="TP-3", level=3, department_id=dept.id
    )
    pos = await svc.create(pos_in)
    upd = PositionUpdate(department_id=uuid4())
    with pytest.raises(Exception) as exc:
        await svc.update(pos.id, upd)
    assert "Department not found" in str(exc.value)
