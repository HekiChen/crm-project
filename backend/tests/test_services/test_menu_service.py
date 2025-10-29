"""
Tests for menu service business logic.
"""
import pytest
from fastapi import HTTPException

from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate


@pytest.mark.asyncio
async def test_create_menu(menu_service, db_session):
    """Test creating a menu successfully."""
    schema = MenuCreate(
        name="Dashboard",
        path="/dashboard",
        icon="dashboard-icon",
        sort_order=1,
        menu_type="frontend"
    )
    menu = await menu_service.create(schema)
    
    assert menu.id is not None
    assert menu.name == "Dashboard"
    assert menu.path == "/dashboard"
    assert menu.is_active == True


@pytest.mark.asyncio
async def test_create_menu_duplicate_path(menu_service, db_session):
    """Test creating menu with duplicate path raises 409."""
    schema1 = MenuCreate(name="Menu 1", path="/test")
    await menu_service.create(schema1)
    
    schema2 = MenuCreate(name="Menu 2", path="/test")
    with pytest.raises(HTTPException) as exc_info:
        await menu_service.create(schema2)
    assert exc_info.value.status_code == 409
    assert "path" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_menu_with_parent(menu_service, db_session):
    """Test creating menu with parent relationship."""
    # Create parent
    parent_schema = MenuCreate(name="Parent", path="/parent")
    parent = await menu_service.create(parent_schema)
    
    # Create child
    child_schema = MenuCreate(name="Child", path="/parent/child", parent_id=parent.id)
    child = await menu_service.create(child_schema)
    
    assert child.parent_id == parent.id


@pytest.mark.asyncio
async def test_create_menu_nonexistent_parent(menu_service, db_session):
    """Test creating menu with non-existent parent raises 404."""
    import uuid
    fake_id = uuid.uuid4()
    
    schema = MenuCreate(name="Child", path="/child", parent_id=fake_id)
    with pytest.raises(HTTPException) as exc_info:
        await menu_service.create(schema)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_by_path(menu_service, db_session):
    """Test getting menu by path."""
    schema = MenuCreate(name="Test", path="/test-path")
    created = await menu_service.create(schema)
    
    found = await menu_service.get_by_path("/test-path")
    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_update_menu(menu_service, db_session):
    """Test updating menu successfully."""
    schema = MenuCreate(name="Original", path="/original")
    menu = await menu_service.create(schema)
    
    update_schema = MenuUpdate(name="Updated", path="/updated")
    updated = await menu_service.update(menu.id, update_schema)
    
    assert updated.name == "Updated"
    assert updated.path == "/updated"


@pytest.mark.asyncio
async def test_update_menu_duplicate_path(menu_service, db_session):
    """Test updating menu to duplicate path raises 409."""
    menu1 = await menu_service.create(MenuCreate(name="Menu 1", path="/path1"))
    menu2 = await menu_service.create(MenuCreate(name="Menu 2", path="/path2"))
    
    with pytest.raises(HTTPException) as exc_info:
        await menu_service.update(menu2.id, MenuUpdate(path="/path1"))
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_update_menu_self_parent(menu_service, db_session):
    """Test menu cannot be its own parent."""
    menu = await menu_service.create(MenuCreate(name="Test", path="/test"))
    
    with pytest.raises(HTTPException) as exc_info:
        await menu_service.update(menu.id, MenuUpdate(parent_id=menu.id))
    assert exc_info.value.status_code == 409
    assert "own parent" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_circular_reference_detection(menu_service, db_session):
    """Test circular reference detection in hierarchy."""
    # Create A -> B -> C
    menu_a = await menu_service.create(MenuCreate(name="A", path="/a"))
    menu_b = await menu_service.create(MenuCreate(name="B", path="/b", parent_id=menu_a.id))
    menu_c = await menu_service.create(MenuCreate(name="C", path="/c", parent_id=menu_b.id))
    
    # Try to make A's parent = C (would create cycle)
    with pytest.raises(HTTPException) as exc_info:
        await menu_service.update(menu_a.id, MenuUpdate(parent_id=menu_c.id))
    assert exc_info.value.status_code == 409
    assert "circular" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_children(menu_service, db_session):
    """Test getting children of a menu."""
    parent = await menu_service.create(MenuCreate(name="Parent", path="/parent"))
    child1 = await menu_service.create(MenuCreate(name="Child 1", path="/parent/child1", parent_id=parent.id, sort_order=2))
    child2 = await menu_service.create(MenuCreate(name="Child 2", path="/parent/child2", parent_id=parent.id, sort_order=1))
    
    children = await menu_service.get_children(parent.id)
    
    assert len(children) == 2
    # Should be sorted by sort_order, so Child 2 comes first
    assert children[0].name == "Child 2"
    assert children[1].name == "Child 1"


@pytest.mark.asyncio
async def test_get_tree(menu_service, db_session):
    """Test getting menu tree structure."""
    # Create hierarchy: Root -> Child1, Child2; Child1 -> Grandchild
    root = await menu_service.create(MenuCreate(name="Root", path="/root", sort_order=1))
    child1 = await menu_service.create(MenuCreate(name="Child 1", path="/root/child1", parent_id=root.id, sort_order=1))
    child2 = await menu_service.create(MenuCreate(name="Child 2", path="/root/child2", parent_id=root.id, sort_order=2))
    grandchild = await menu_service.create(MenuCreate(name="Grandchild", path="/root/child1/grand", parent_id=child1.id))
    
    tree = await menu_service.get_tree()
    
    assert len(tree) == 1  # One root
    assert tree[0].name == "Root"
    assert len(tree[0].children) == 2  # Two children
    assert tree[0].children[0].name == "Child 1"
    assert len(tree[0].children[0].children) == 1  # One grandchild
    assert tree[0].children[0].children[0].name == "Grandchild"


@pytest.mark.asyncio
async def test_get_list_with_filters(menu_service, db_session):
    """Test getting paginated list with filters."""
    from app.schemas.base import PaginationParams
    
    # Create menus with different types
    await menu_service.create(MenuCreate(name="Frontend 1", path="/fe1", menu_type="frontend"))
    await menu_service.create(MenuCreate(name="Backend 1", path="/be1", menu_type="backend"))
    await menu_service.create(MenuCreate(name="Frontend 2", path="/fe2", menu_type="frontend"))
    
    # Filter by menu_type
    params = PaginationParams(page=1, page_size=10)
    result = await menu_service.get_list(pagination=params, filters={"menu_type": "frontend"})
    
    assert result.total == 2
    assert all(item.menu_type == "frontend" for item in result.data)


@pytest.mark.asyncio
async def test_delete_menu(menu_service, db_session):
    """Test soft-deleting a menu."""
    menu = await menu_service.create(MenuCreate(name="To Delete", path="/delete"))
    
    success = await menu_service.delete(menu.id)
    assert success == True
    
    # Should not be found without include_deleted
    found = await menu_service.get_by_id(menu.id)
    assert found is None
    
    # Should be found with include_deleted
    found_deleted = await menu_service.get_by_id(menu.id, include_deleted=True)
    assert found_deleted is not None
    assert found_deleted.is_deleted == True


@pytest.mark.asyncio
async def test_menu_type_validation(menu_service, db_session):
    """Test menu_type validation in schema."""
    # Valid types should work
    for menu_type in ["frontend", "backend", "api"]:
        schema = MenuCreate(name=f"Test {menu_type}", path=f"/{menu_type}", menu_type=menu_type)
        menu = await menu_service.create(schema)
        assert menu.menu_type == menu_type
