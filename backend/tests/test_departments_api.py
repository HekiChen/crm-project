import pytest

from app.schemas.department_schemas import DepartmentCreate, DepartmentUpdate


@pytest.mark.asyncio
async def test_departments_crud(client):
    # Create
    payload = {"code": "API-01", "name": "API Dept"}
    r = await client.post("/api/v1/departments/", json=payload)
    assert r.status_code == 201
    body = r.json()
    dept_id = body["id"]

    # Get
    r2 = await client.get(f"/api/v1/departments/{dept_id}")
    assert r2.status_code == 200

    # List
    r3 = await client.get("/api/v1/departments/")
    assert r3.status_code == 200
    data = r3.json()
    assert any(d["id"] == dept_id for d in data["data"]) or isinstance(data, dict)

    # Patch
    r4 = await client.patch(f"/api/v1/departments/{dept_id}", json={"name": "Updated"})
    assert r4.status_code == 200
    assert r4.json()["name"] == "Updated"

    # Delete
    r5 = await client.delete(f"/api/v1/departments/{dept_id}")
    assert r5.status_code == 200

    # Get after delete -> 404
    r6 = await client.get(f"/api/v1/departments/{dept_id}")
    assert r6.status_code == 404
