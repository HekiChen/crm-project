"""
Tests for role API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_roles_crud(client):
    """Test complete CRUD operations for roles."""
    # Create role
    payload = {
        "name": "Test API Role",
        "code": "TEST_API_ROLE",
        "description": "Role created via API"
    }
    r = await client.post("/api/v1/roles/", json=payload)
    assert r.status_code == 201
    body = r.json()
    role_id = body["data"]["id"]
    assert body["data"]["name"] == "Test API Role"
    assert body["data"]["code"] == "TEST_API_ROLE"
    assert body["data"]["is_system_role"] == False

    # Get role by ID
    r2 = await client.get(f"/api/v1/roles/{role_id}")
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == role_id

    # List roles
    r3 = await client.get("/api/v1/roles/")
    assert r3.status_code == 200
    response = r3.json()
    assert "data" in response
    # Response format: {"data": {"data": [...], "total": ..., ...}}
    list_data = response["data"]
    if isinstance(list_data, dict) and "data" in list_data:
        items = list_data["data"]
    elif isinstance(list_data, list):
        items = list_data
    else:
        raise AssertionError(f"Unexpected data format: {type(list_data)}")
    assert any(role["id"] == role_id for role in items)

    # Update role
    r4 = await client.patch(
        f"/api/v1/roles/{role_id}",
        json={"name": "Updated API Role", "description": "Updated"}
    )
    assert r4.status_code == 200
    assert r4.json()["data"]["name"] == "Updated API Role"
    assert r4.json()["data"]["description"] == "Updated"
    assert r4.json()["data"]["code"] == "TEST_API_ROLE"  # Code should not change

    # Delete role
    r5 = await client.delete(f"/api/v1/roles/{role_id}")
    assert r5.status_code == 200

    # Get after delete -> 404
    r6 = await client.get(f"/api/v1/roles/{role_id}")
    assert r6.status_code == 404


@pytest.mark.asyncio
async def test_create_role_duplicate_name(client):
    """Test creating role with duplicate name returns 409."""
    payload = {
        "name": "Duplicate Name Role",
        "code": "DUP_NAME_1"
    }
    r1 = await client.post("/api/v1/roles/", json=payload)
    assert r1.status_code == 201

    # Try with same name but different code
    payload2 = {
        "name": "Duplicate Name Role",
        "code": "DUP_NAME_2"
    }
    r2 = await client.post("/api/v1/roles/", json=payload2)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_create_role_duplicate_code(client):
    """Test creating role with duplicate code returns 409."""
    payload = {
        "name": "First Role",
        "code": "DUPLICATE_CODE"
    }
    r1 = await client.post("/api/v1/roles/", json=payload)
    assert r1.status_code == 201

    # Try with same code but different name
    payload2 = {
        "name": "Second Role",
        "code": "DUPLICATE_CODE"
    }
    r2 = await client.post("/api/v1/roles/", json=payload2)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_update_role_duplicate_name(client):
    """Test updating role to duplicate name returns 409."""
    # Create first role
    r1 = await client.post("/api/v1/roles/", json={"name": "Role One", "code": "ROLE_1"})
    assert r1.status_code == 201

    # Create second role
    r2 = await client.post("/api/v1/roles/", json={"name": "Role Two", "code": "ROLE_2"})
    assert r2.status_code == 201
    role2_id = r2.json()["data"]["id"]

    # Try to update role2 with role1's name
    r3 = await client.patch(f"/api/v1/roles/{role2_id}", json={"name": "Role One"})
    assert r3.status_code == 409


@pytest.mark.asyncio
async def test_delete_system_role_fails(client, db_session):
    """Test deleting a system role returns 409."""
    from app.models.role import Role
    
    # Create a system role directly
    system_role = Role(
        name="System Admin",
        code="SYS_ADMIN",
        is_system_role=True
    )
    db_session.add(system_role)
    await db_session.commit()
    await db_session.refresh(system_role)
    
    # Try to delete it via API
    r = await client.delete(f"/api/v1/roles/{system_role.id}")
    assert r.status_code == 409
    error_body = r.json()
    assert "error" in error_body
    assert "system" in error_body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_get_nonexistent_role(client):
    """Test getting non-existent role returns 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    r = await client.get(f"/api/v1/roles/{fake_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_roles_with_filter(client, db_session):
    """Test listing roles with is_system_role filter."""
    from app.models.role import Role
    
    # Create custom role
    r1 = await client.post("/api/v1/roles/", json={"name": "Custom", "code": "CUSTOM"})
    assert r1.status_code == 201
    
    # Create system role directly
    system_role = Role(name="System", code="SYSTEM", is_system_role=True)
    db_session.add(system_role)
    await db_session.commit()
    
    # Filter for system roles only
    r2 = await client.get("/api/v1/roles/?is_system_role=true")
    assert r2.status_code == 200
    response = r2.json()
    # Response format: {"data": {"data": [...], "total": ..., ...}}
    items = response["data"]["data"] if isinstance(response["data"], dict) and "data" in response["data"] else response["data"]
    assert all(role["is_system_role"] for role in items)
    
    # Filter for custom roles only
    r3 = await client.get("/api/v1/roles/?is_system_role=false")
    assert r3.status_code == 200
    response = r3.json()
    items = response["data"]["data"] if isinstance(response["data"], dict) and "data" in response["data"] else response["data"]
    assert all(not role["is_system_role"] for role in items)


@pytest.mark.asyncio
async def test_get_role_permissions(client):
    """Test getting role's menu permissions."""
    # Create role
    r1 = await client.post("/api/v1/roles/", json={"name": "Perm Test", "code": "PERM_TEST"})
    assert r1.status_code == 201
    role_id = r1.json()["data"]["id"]
    
    # Get permissions (should be empty initially)
    r2 = await client.get(f"/api/v1/roles/{role_id}/permissions")
    assert r2.status_code == 200
    # Response is wrapped: {"data": [], "meta": {...}}
    response = r2.json()
    assert "data" in response
    assert isinstance(response["data"], list)


@pytest.mark.asyncio
async def test_get_role_employees(client):
    """Test getting role's assigned employees."""
    # Create role
    r1 = await client.post("/api/v1/roles/", json={"name": "Emp Test", "code": "EMP_TEST"})
    assert r1.status_code == 201
    role_id = r1.json()["data"]["id"]
    
    # Get employees (should be empty initially)
    r2 = await client.get(f"/api/v1/roles/{role_id}/employees")
    assert r2.status_code == 200
    # Response is wrapped: {"data": [], "meta": {...}}
    response = r2.json()
    assert "data" in response
    assert isinstance(response["data"], list)


@pytest.mark.asyncio
async def test_create_role_permission(client):
    """Test creating a single permission for a role."""
    # Create role
    r1 = await client.post("/api/v1/roles/", json={"name": "Perm Create Role", "code": "PERM_CREATE"})
    assert r1.status_code == 201
    role_id = r1.json()["data"]["id"]
    
    # Create menu
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Test Menu",
        "path": "/test-perm",
        "menu_type": "frontend"
    })
    assert r2.status_code == 201
    menu_id = r2.json()["data"]["id"]
    
    # Create permission
    r3 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": role_id,
        "menu_id": menu_id,
        "can_read": True,
        "can_write": True,
        "can_delete": False
    })
    assert r3.status_code == 201
    perm_data = r3.json()["data"]
    assert perm_data["role_id"] == role_id
    assert perm_data["menu_id"] == menu_id
    assert perm_data["can_read"] is True
    assert perm_data["can_write"] is True
    assert perm_data["can_delete"] is False


@pytest.mark.asyncio
async def test_create_role_permission_role_mismatch(client):
    """Test creating permission with mismatched role_id fails."""
    # Create role
    r1 = await client.post("/api/v1/roles/", json={"name": "Role A", "code": "ROLE_A"})
    assert r1.status_code == 201
    role_id = r1.json()["data"]["id"]
    
    # Create another role
    r2 = await client.post("/api/v1/roles/", json={"name": "Role B", "code": "ROLE_B"})
    assert r2.status_code == 201
    other_role_id = r2.json()["data"]["id"]
    
    # Create menu
    r3 = await client.post("/api/v1/menus/", json={
        "name": "Test Menu",
        "path": "/test-mismatch",
        "menu_type": "frontend"
    })
    assert r3.status_code == 201
    menu_id = r3.json()["data"]["id"]
    
    # Try to create permission with mismatched role_id
    r4 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": other_role_id,  # Different from URL
        "menu_id": menu_id,
        "can_read": True,
        "can_write": False,
        "can_delete": False
    })
    assert r4.status_code == 400
    assert "must match" in r4.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_create_duplicate_permission(client):
    """Test creating duplicate permission fails."""
    # Create role and menu
    r1 = await client.post("/api/v1/roles/", json={"name": "Dup Role", "code": "DUP_ROLE"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Dup Menu",
        "path": "/dup-menu",
        "menu_type": "frontend"
    })
    menu_id = r2.json()["data"]["id"]
    
    # Create first permission
    r3 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": role_id,
        "menu_id": menu_id,
        "can_read": True,
        "can_write": False,
        "can_delete": False
    })
    assert r3.status_code == 201
    
    # Try to create duplicate
    r4 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": role_id,
        "menu_id": menu_id,
        "can_read": True,
        "can_write": True,
        "can_delete": True
    })
    assert r4.status_code == 409
    assert "already exists" in r4.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_batch_create_permissions(client):
    """Test batch creating permissions for a role."""
    # Create role
    r1 = await client.post("/api/v1/roles/", json={"name": "Batch Role", "code": "BATCH_ROLE"})
    role_id = r1.json()["data"]["id"]
    
    # Create multiple menus
    menu_ids = []
    for i in range(3):
        r = await client.post("/api/v1/menus/", json={
            "name": f"Batch Menu {i}",
            "path": f"/batch-menu-{i}",
            "menu_type": "frontend"
        })
        assert r.status_code == 201
        menu_ids.append(r.json()["data"]["id"])
    
    # Batch create permissions
    r2 = await client.post(f"/api/v1/roles/{role_id}/permissions/batch", json={
        "role_id": role_id,
        "permissions": [
            {"menu_id": menu_ids[0], "can_read": True, "can_write": False, "can_delete": False},
            {"menu_id": menu_ids[1], "can_read": True, "can_write": True, "can_delete": False},
            {"menu_id": menu_ids[2], "can_read": True, "can_write": True, "can_delete": True},
        ]
    })
    assert r2.status_code == 201
    perms = r2.json()["data"]
    assert len(perms) == 3
    
    # Verify permissions were created
    r3 = await client.get(f"/api/v1/roles/{role_id}/permissions")
    assert r3.status_code == 200
    all_perms = r3.json()["data"]
    assert len(all_perms) == 3


@pytest.mark.asyncio
async def test_batch_create_role_mismatch(client):
    """Test batch create with mismatched role_id fails."""
    # Create two roles
    r1 = await client.post("/api/v1/roles/", json={"name": "Role 1", "code": "ROLE_1"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/roles/", json={"name": "Role 2", "code": "ROLE_2"})
    other_role_id = r2.json()["data"]["id"]
    
    # Try batch create with mismatched role_id
    r3 = await client.post(f"/api/v1/roles/{role_id}/permissions/batch", json={
        "role_id": other_role_id,  # Different from URL
        "permissions": []
    })
    assert r3.status_code == 400
    assert "must match" in r3.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_update_role_permission(client):
    """Test updating an existing permission."""
    # Create role and menu
    r1 = await client.post("/api/v1/roles/", json={"name": "Update Role", "code": "UPDATE_ROLE"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Update Menu",
        "path": "/update-menu",
        "menu_type": "frontend"
    })
    menu_id = r2.json()["data"]["id"]
    
    # Create permission
    r3 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": role_id,
        "menu_id": menu_id,
        "can_read": True,
        "can_write": False,
        "can_delete": False
    })
    assert r3.status_code == 201
    
    # Update permission
    r4 = await client.patch(f"/api/v1/roles/{role_id}/permissions/{menu_id}", json={
        "can_write": True,
        "can_delete": True
    })
    assert r4.status_code == 200
    perm_data = r4.json()["data"]
    assert perm_data["can_read"] is True  # Unchanged
    assert perm_data["can_write"] is True  # Updated
    assert perm_data["can_delete"] is True  # Updated


@pytest.mark.asyncio
async def test_update_nonexistent_permission(client):
    """Test updating non-existent permission returns 404."""
    # Create role and menu
    r1 = await client.post("/api/v1/roles/", json={"name": "Role X", "code": "ROLE_X"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Menu X",
        "path": "/menu-x",
        "menu_type": "frontend"
    })
    menu_id = r2.json()["data"]["id"]
    
    # Try to update non-existent permission
    r3 = await client.patch(f"/api/v1/roles/{role_id}/permissions/{menu_id}", json={
        "can_write": True
    })
    assert r3.status_code == 404
    assert "not found" in r3.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_delete_role_permission(client):
    """Test deleting a permission."""
    # Create role and menu
    r1 = await client.post("/api/v1/roles/", json={"name": "Delete Role", "code": "DELETE_ROLE"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Delete Menu",
        "path": "/delete-menu",
        "menu_type": "frontend"
    })
    menu_id = r2.json()["data"]["id"]
    
    # Create permission
    r3 = await client.post(f"/api/v1/roles/{role_id}/permissions", json={
        "role_id": role_id,
        "menu_id": menu_id,
        "can_read": True,
        "can_write": False,
        "can_delete": False
    })
    assert r3.status_code == 201
    
    # Delete permission
    r4 = await client.delete(f"/api/v1/roles/{role_id}/permissions/{menu_id}")
    assert r4.status_code == 200
    assert "deleted successfully" in r4.json()["data"]["message"].lower()
    
    # Verify it's deleted
    r5 = await client.get(f"/api/v1/roles/{role_id}/permissions")
    assert r5.status_code == 200
    perms = r5.json()["data"]
    assert len(perms) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_permission(client):
    """Test deleting non-existent permission returns 404."""
    # Create role and menu
    r1 = await client.post("/api/v1/roles/", json={"name": "Role Y", "code": "ROLE_Y"})
    role_id = r1.json()["data"]["id"]
    
    r2 = await client.post("/api/v1/menus/", json={
        "name": "Menu Y",
        "path": "/menu-y",
        "menu_type": "frontend"
    })
    menu_id = r2.json()["data"]["id"]
    
    # Try to delete non-existent permission
    r3 = await client.delete(f"/api/v1/roles/{role_id}/permissions/{menu_id}")
    assert r3.status_code == 404
    assert "not found" in r3.json()["error"]["message"].lower()

