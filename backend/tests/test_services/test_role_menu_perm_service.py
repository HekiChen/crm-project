"""
Tests for RoleMenuPermService
"""
import pytest
from uuid import uuid4

from app.services.role_menu_perm_service import RoleMenuPermService
from app.services.role_service import RoleService
from app.services.menu_service import MenuService
from app.schemas.role_menu_perm import RoleMenuPermCreate, RoleMenuPermUpdate


@pytest.mark.asyncio
async def test_create_permission(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test creating a role-menu permission."""
    # Create role and menu
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    # Create permission
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=True,
        can_delete=False
    )
    perm = await role_menu_perm_service.create(perm_data)
    
    assert perm is not None
    assert perm.role_id == role.id
    assert perm.menu_id == menu.id
    assert perm.can_read is True
    assert perm.can_write is True
    assert perm.can_delete is False


@pytest.mark.asyncio
async def test_create_permission_role_not_found(role_menu_perm_service: RoleMenuPermService, menu_service: MenuService):
    """Test creating permission with non-existent role."""
    from app.schemas.menu import MenuCreate
    
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=uuid4(),
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    
    with pytest.raises(Exception) as exc_info:
        await role_menu_perm_service.create(perm_data)
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_permission_menu_not_found(role_menu_perm_service: RoleMenuPermService, role_service: RoleService):
    """Test creating permission with non-existent menu."""
    from app.schemas.role import RoleCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=uuid4(),
        can_read=True,
        can_write=False,
        can_delete=False
    )
    
    with pytest.raises(Exception) as exc_info:
        await role_menu_perm_service.create(perm_data)
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_create_duplicate_permission(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test creating duplicate permission fails."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    # Create first permission
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    await role_menu_perm_service.create(perm_data)
    
    # Try to create duplicate
    with pytest.raises(Exception) as exc_info:
        await role_menu_perm_service.create(perm_data)
    
    assert exc_info.value.status_code == 409
    assert "already exists" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_get_by_id(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test getting permission by ID."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    created = await role_menu_perm_service.create(perm_data)
    
    # Get by ID
    found = await role_menu_perm_service.get_by_id(created.id)
    
    assert found is not None
    assert found.id == created.id
    assert found.role_id == role.id
    assert found.menu_id == menu.id


@pytest.mark.asyncio
async def test_get_by_role_and_menu(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test getting permission by role and menu IDs."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    created = await role_menu_perm_service.create(perm_data)
    
    # Get by role and menu
    found = await role_menu_perm_service.get_by_role_and_menu(role.id, menu.id)
    
    assert found is not None
    assert found.id == created.id
    assert found.role_id == role.id
    assert found.menu_id == menu.id


@pytest.mark.asyncio
async def test_batch_create(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test batch creating permissions."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu1 = await menu_service.create(MenuCreate(
        name="Menu 1",
        path="/menu1",
        menu_type="frontend"
    ))
    menu2 = await menu_service.create(MenuCreate(
        name="Menu 2",
        path="/menu2",
        menu_type="frontend"
    ))
    menu3 = await menu_service.create(MenuCreate(
        name="Menu 3",
        path="/menu3",
        menu_type="frontend"
    ))
    
    # Batch create permissions
    permissions_data = [
        {"menu_id": menu1.id, "can_read": True, "can_write": False, "can_delete": False},
        {"menu_id": menu2.id, "can_read": True, "can_write": True, "can_delete": False},
        {"menu_id": menu3.id, "can_read": True, "can_write": True, "can_delete": True},
    ]
    
    created = await role_menu_perm_service.batch_create(role.id, permissions_data)
    
    assert len(created) == 3
    assert created[0].menu_id == menu1.id
    assert created[0].can_write is False
    assert created[1].menu_id == menu2.id
    assert created[1].can_write is True
    assert created[2].menu_id == menu3.id
    assert created[2].can_delete is True


@pytest.mark.asyncio
async def test_batch_create_skips_existing(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test batch create skips existing permissions."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu1 = await menu_service.create(MenuCreate(
        name="Menu 1",
        path="/menu1",
        menu_type="frontend"
    ))
    menu2 = await menu_service.create(MenuCreate(
        name="Menu 2",
        path="/menu2",
        menu_type="frontend"
    ))
    
    # Create one permission manually
    await role_menu_perm_service.create(RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu1.id,
        can_read=True,
        can_write=False,
        can_delete=False
    ))
    
    # Batch create with duplicate
    permissions_data = [
        {"menu_id": menu1.id, "can_read": True, "can_write": True, "can_delete": False},  # Duplicate
        {"menu_id": menu2.id, "can_read": True, "can_write": True, "can_delete": False},
    ]
    
    created = await role_menu_perm_service.batch_create(role.id, permissions_data)
    
    # Should only create menu2 permission
    assert len(created) == 1
    assert created[0].menu_id == menu2.id


@pytest.mark.asyncio
async def test_batch_create_role_not_found(role_menu_perm_service: RoleMenuPermService):
    """Test batch create with non-existent role."""
    permissions_data = [
        {"menu_id": uuid4(), "can_read": True, "can_write": False, "can_delete": False},
    ]
    
    with pytest.raises(Exception) as exc_info:
        await role_menu_perm_service.batch_create(uuid4(), permissions_data)
    
    assert exc_info.value.status_code == 404
    assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_update_permission(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test updating a permission."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    created = await role_menu_perm_service.create(perm_data)
    
    # Update permission
    update_data = RoleMenuPermUpdate(can_write=True, can_delete=True)
    updated = await role_menu_perm_service.update(created.id, update_data)
    
    assert updated is not None
    assert updated.id == created.id
    assert updated.can_read is True
    assert updated.can_write is True
    assert updated.can_delete is True


@pytest.mark.asyncio
async def test_update_by_role_and_menu(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test updating permission by role and menu IDs."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    created = await role_menu_perm_service.create(perm_data)
    
    # Update by role and menu
    update_data = RoleMenuPermUpdate(can_write=True)
    updated = await role_menu_perm_service.update_by_role_and_menu(role.id, menu.id, update_data)
    
    assert updated is not None
    assert updated.id == created.id
    assert updated.can_write is True


@pytest.mark.asyncio
async def test_delete_permission(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test deleting a permission."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    created = await role_menu_perm_service.create(perm_data)
    
    # Delete permission
    deleted = await role_menu_perm_service.delete(created.id)
    
    assert deleted is True
    
    # Verify it's soft deleted
    found = await role_menu_perm_service.get_by_id(created.id)
    assert found is None


@pytest.mark.asyncio
async def test_delete_by_role_and_menu(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test deleting permission by role and menu IDs."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    perm_data = RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    )
    await role_menu_perm_service.create(perm_data)
    
    # Delete by role and menu
    deleted = await role_menu_perm_service.delete_by_role_and_menu(role.id, menu.id)
    
    assert deleted is True
    
    # Verify it's deleted
    found = await role_menu_perm_service.get_by_role_and_menu(role.id, menu.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_role(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test getting all permissions for a role."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role = await role_service.create(RoleCreate(name="Test Role", code="TEST_ROLE"))
    menu1 = await menu_service.create(MenuCreate(
        name="Menu 1",
        path="/menu1",
        menu_type="frontend"
    ))
    menu2 = await menu_service.create(MenuCreate(
        name="Menu 2",
        path="/menu2",
        menu_type="frontend"
    ))
    
    # Create permissions
    await role_menu_perm_service.create(RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu1.id,
        can_read=True,
        can_write=False,
        can_delete=False
    ))
    await role_menu_perm_service.create(RoleMenuPermCreate(
        role_id=role.id,
        menu_id=menu2.id,
        can_read=True,
        can_write=True,
        can_delete=False
    ))
    
    # Get by role
    perms = await role_menu_perm_service.get_by_role(role.id)
    
    assert len(perms) == 2
    assert all(p.role_id == role.id for p in perms)
    menu_ids = {p.menu_id for p in perms}
    assert menu1.id in menu_ids
    assert menu2.id in menu_ids


@pytest.mark.asyncio
async def test_get_by_menu(role_menu_perm_service: RoleMenuPermService, role_service: RoleService, menu_service: MenuService):
    """Test getting all permissions for a menu."""
    from app.schemas.role import RoleCreate
    from app.schemas.menu import MenuCreate
    
    role1 = await role_service.create(RoleCreate(name="Role 1", code="ROLE1"))
    role2 = await role_service.create(RoleCreate(name="Role 2", code="ROLE2"))
    menu = await menu_service.create(MenuCreate(
        name="Test Menu",
        path="/test",
        menu_type="frontend"
    ))
    
    # Create permissions
    await role_menu_perm_service.create(RoleMenuPermCreate(
        role_id=role1.id,
        menu_id=menu.id,
        can_read=True,
        can_write=False,
        can_delete=False
    ))
    await role_menu_perm_service.create(RoleMenuPermCreate(
        role_id=role2.id,
        menu_id=menu.id,
        can_read=True,
        can_write=True,
        can_delete=True
    ))
    
    # Get by menu
    perms = await role_menu_perm_service.get_by_menu(menu.id)
    
    assert len(perms) == 2
    assert all(p.menu_id == menu.id for p in perms)
    role_ids = {p.role_id for p in perms}
    assert role1.id in role_ids
    assert role2.id in role_ids
