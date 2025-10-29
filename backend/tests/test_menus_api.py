"""
Tests for menu API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_menus_crud(client):
    """Test complete CRUD operations for menus."""
    # Create menu
    payload = {
        "name": "Dashboard",
        "path": "/dashboard",
        "icon": "dashboard-icon",
        "menu_type": "frontend",
        "sort_order": 1
    }
    r = await client.post("/api/v1/menus/", json=payload)
    assert r.status_code == 201
    body = r.json()
    menu_id = body["data"]["id"]
    assert body["data"]["name"] == "Dashboard"
    assert body["data"]["path"] == "/dashboard"
    assert body["data"]["is_active"] == True

    # Get menu by ID
    r2 = await client.get(f"/api/v1/menus/{menu_id}")
    assert r2.status_code == 200
    assert r2.json()["data"]["id"] == menu_id

    # List menus
    r3 = await client.get("/api/v1/menus/")
    assert r3.status_code == 200
    response = r3.json()
    assert "data" in response
    items = response["data"]["data"]
    assert any(menu["id"] == menu_id for menu in items)

    # Update menu
    r4 = await client.patch(
        f"/api/v1/menus/{menu_id}",
        json={"name": "Updated Dashboard", "is_active": False}
    )
    assert r4.status_code == 200
    assert r4.json()["data"]["name"] == "Updated Dashboard"
    assert r4.json()["data"]["is_active"] == False

    # Delete menu
    r5 = await client.delete(f"/api/v1/menus/{menu_id}")
    assert r5.status_code == 200

    # Get after delete -> 404
    r6 = await client.get(f"/api/v1/menus/{menu_id}")
    assert r6.status_code == 404


@pytest.mark.asyncio
async def test_create_menu_duplicate_path(client):
    """Test creating menu with duplicate path returns 409."""
    payload = {
        "name": "Menu 1",
        "path": "/duplicate-path"
    }
    r1 = await client.post("/api/v1/menus/", json=payload)
    assert r1.status_code == 201

    # Try with same path but different name
    payload2 = {
        "name": "Menu 2",
        "path": "/duplicate-path"
    }
    r2 = await client.post("/api/v1/menus/", json=payload2)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_create_menu_with_parent(client):
    """Test creating menu with parent relationship."""
    # Create parent
    parent_payload = {
        "name": "Parent Menu",
        "path": "/parent"
    }
    r1 = await client.post("/api/v1/menus/", json=parent_payload)
    assert r1.status_code == 201
    parent_id = r1.json()["data"]["id"]

    # Create child
    child_payload = {
        "name": "Child Menu",
        "path": "/parent/child",
        "parent_id": parent_id
    }
    r2 = await client.post("/api/v1/menus/", json=child_payload)
    assert r2.status_code == 201
    assert r2.json()["data"]["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_create_menu_nonexistent_parent(client):
    """Test creating menu with non-existent parent raises 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    
    payload = {
        "name": "Child",
        "path": "/child",
        "parent_id": fake_id
    }
    r = await client.post("/api/v1/menus/", json=payload)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_menu_duplicate_path(client):
    """Test updating menu to duplicate path returns 409."""
    menu1 = await client.post("/api/v1/menus/", json={"name": "Menu 1", "path": "/path1"})
    assert menu1.status_code == 201
    
    menu2 = await client.post("/api/v1/menus/", json={"name": "Menu 2", "path": "/path2"})
    assert menu2.status_code == 201
    menu2_id = menu2.json()["data"]["id"]

    r = await client.patch(f"/api/v1/menus/{menu2_id}", json={"path": "/path1"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_menu_self_parent(client):
    """Test menu cannot be its own parent."""
    menu = await client.post("/api/v1/menus/", json={"name": "Test", "path": "/test"})
    assert menu.status_code == 201
    menu_id = menu.json()["data"]["id"]

    r = await client.patch(f"/api/v1/menus/{menu_id}", json={"parent_id": menu_id})
    assert r.status_code == 409
    error_body = r.json()
    assert "error" in error_body
    assert "own parent" in error_body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_circular_reference_prevention(client):
    """Test circular reference detection in hierarchy."""
    # Create A -> B -> C
    r_a = await client.post("/api/v1/menus/", json={"name": "A", "path": "/a"})
    menu_a_id = r_a.json()["data"]["id"]
    
    r_b = await client.post("/api/v1/menus/", json={"name": "B", "path": "/b", "parent_id": menu_a_id})
    menu_b_id = r_b.json()["data"]["id"]
    
    r_c = await client.post("/api/v1/menus/", json={"name": "C", "path": "/c", "parent_id": menu_b_id})
    menu_c_id = r_c.json()["data"]["id"]

    # Try to make A's parent = C (would create cycle)
    r = await client.patch(f"/api/v1/menus/{menu_a_id}", json={"parent_id": menu_c_id})
    assert r.status_code == 409
    error_body = r.json()
    assert "error" in error_body
    assert "circular" in error_body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_get_nonexistent_menu(client):
    """Test getting non-existent menu returns 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    r = await client.get(f"/api/v1/menus/{fake_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_menus_with_filter(client):
    """Test listing menus with filters."""
    # Create menus with different types
    await client.post("/api/v1/menus/", json={"name": "FE1", "path": "/fe1", "menu_type": "frontend"})
    await client.post("/api/v1/menus/", json={"name": "BE1", "path": "/be1", "menu_type": "backend"})
    await client.post("/api/v1/menus/", json={"name": "FE2", "path": "/fe2", "menu_type": "frontend"})
    
    # Filter by menu_type
    r = await client.get("/api/v1/menus/?menu_type=frontend")
    assert r.status_code == 200
    response = r.json()
    items = response["data"]["data"]
    assert all(menu["menu_type"] == "frontend" for menu in items)


@pytest.mark.asyncio
async def test_list_menus_filter_by_parent(client):
    """Test filtering menus by parent_id."""
    # Create parent
    r_parent = await client.post("/api/v1/menus/", json={"name": "Parent", "path": "/parent"})
    parent_id = r_parent.json()["data"]["id"]
    
    # Create children
    await client.post("/api/v1/menus/", json={"name": "Child1", "path": "/parent/child1", "parent_id": parent_id})
    await client.post("/api/v1/menus/", json={"name": "Child2", "path": "/parent/child2", "parent_id": parent_id})
    
    # Create root menu
    await client.post("/api/v1/menus/", json={"name": "Root", "path": "/root"})
    
    # Filter by parent_id
    r = await client.get(f"/api/v1/menus/?parent_id={parent_id}")
    assert r.status_code == 200
    response = r.json()
    items = response["data"]["data"]
    assert len(items) == 2
    assert all(menu["parent_id"] == parent_id for menu in items)


@pytest.mark.asyncio
async def test_get_menu_tree(client):
    """Test getting menu tree structure."""
    # Create hierarchy
    r_root = await client.post("/api/v1/menus/", json={"name": "Root", "path": "/root", "sort_order": 1})
    root_id = r_root.json()["data"]["id"]
    
    r_child1 = await client.post("/api/v1/menus/", json={
        "name": "Child 1", 
        "path": "/root/child1", 
        "parent_id": root_id,
        "sort_order": 1
    })
    child1_id = r_child1.json()["data"]["id"]
    
    await client.post("/api/v1/menus/", json={
        "name": "Child 2",
        "path": "/root/child2",
        "parent_id": root_id,
        "sort_order": 2
    })
    
    await client.post("/api/v1/menus/", json={
        "name": "Grandchild",
        "path": "/root/child1/grand",
        "parent_id": child1_id
    })
    
    # Get full tree
    r = await client.get("/api/v1/menus/tree")
    assert r.status_code == 200
    tree = r.json()["data"]
    
    assert len(tree) >= 1
    root_menu = next((m for m in tree if m["name"] == "Root"), None)
    assert root_menu is not None
    assert len(root_menu["children"]) == 2
    assert root_menu["children"][0]["name"] == "Child 1"
    assert len(root_menu["children"][0]["children"]) == 1
    assert root_menu["children"][0]["children"][0]["name"] == "Grandchild"


@pytest.mark.asyncio
async def test_get_menu_children(client):
    """Test getting immediate children of a menu."""
    # Create parent
    r_parent = await client.post("/api/v1/menus/", json={"name": "Parent", "path": "/parent"})
    parent_id = r_parent.json()["data"]["id"]
    
    # Create children
    await client.post("/api/v1/menus/", json={"name": "Child1", "path": "/parent/child1", "parent_id": parent_id})
    await client.post("/api/v1/menus/", json={"name": "Child2", "path": "/parent/child2", "parent_id": parent_id})
    
    # Get children
    r = await client.get(f"/api/v1/menus/{parent_id}/children")
    assert r.status_code == 200
    children = r.json()["data"]
    assert len(children) == 2
    assert all(isinstance(child, dict) for child in children)


@pytest.mark.asyncio
async def test_get_children_nonexistent_parent(client):
    """Test getting children of non-existent parent returns 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    
    r = await client.get(f"/api/v1/menus/{fake_id}/children")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_menu_type_validation(client):
    """Test menu_type validation."""
    # Invalid menu_type should fail
    r = await client.post("/api/v1/menus/", json={
        "name": "Test",
        "path": "/test",
        "menu_type": "invalid_type"
    })
    assert r.status_code == 422  # Validation error
