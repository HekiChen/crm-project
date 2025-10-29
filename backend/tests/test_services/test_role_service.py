"""
Tests for role service.
"""
import pytest
from uuid import uuid4

from fastapi import HTTPException

from app.models.role import Role
from app.schemas.role import RoleCreate, RoleUpdate
from app.schemas.base import PaginationParams
from app.services.role_service import RoleService


@pytest.mark.asyncio
class TestRoleService:
    """Test role service CRUD operations and business rules."""
    
    async def test_create_role(self, db_session, role_service: RoleService):
        """Test creating a new role."""
        role_data = RoleCreate(
            name="Test Role",
            code="TEST_ROLE",
            description="A test role"
        )
        
        role = await role_service.create(role_data)
        
        assert role.id is not None
        assert role.name == "Test Role"
        assert role.code == "TEST_ROLE"
        assert role.description == "A test role"
        assert role.is_system_role == False
        assert role.is_deleted == False
    
    async def test_create_role_duplicate_name(self, db_session, role_service: RoleService):
        """Test creating role with duplicate name raises 409."""
        role_data = RoleCreate(
            name="Duplicate Role",
            code="DUP1",
            description="First"
        )
        await role_service.create(role_data)
        
        # Try to create with same name but different code
        role_data2 = RoleCreate(
            name="Duplicate Role",
            code="DUP2",
            description="Second"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await role_service.create(role_data2)
        
        assert exc_info.value.status_code == 409
        assert "name" in exc_info.value.detail.lower()
    
    async def test_create_role_duplicate_code(self, db_session, role_service: RoleService):
        """Test creating role with duplicate code raises 409."""
        role_data = RoleCreate(
            name="First Role",
            code="DUPLICATE_CODE",
            description="First"
        )
        await role_service.create(role_data)
        
        # Try to create with same code but different name
        role_data2 = RoleCreate(
            name="Second Role",
            code="DUPLICATE_CODE",
            description="Second"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await role_service.create(role_data2)
        
        assert exc_info.value.status_code == 409
        assert "code" in exc_info.value.detail.lower()
    
    async def test_get_by_id(self, db_session, role_service: RoleService):
        """Test getting role by ID."""
        role_data = RoleCreate(
            name="Get Test Role",
            code="GET_TEST",
            description="Test"
        )
        created = await role_service.create(role_data)
        
        found = await role_service.get_by_id(created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.name == created.name
    
    async def test_get_by_code(self, db_session, role_service: RoleService):
        """Test getting role by code."""
        role_data = RoleCreate(
            name="Code Test Role",
            code="CODE_TEST",
            description="Test"
        )
        created = await role_service.create(role_data)
        
        found = await role_service.get_by_code("CODE_TEST")
        
        assert found is not None
        assert found.id == created.id
        assert found.code == "CODE_TEST"
    
    async def test_update_role(self, db_session, role_service: RoleService):
        """Test updating a role."""
        role_data = RoleCreate(
            name="Original Name",
            code="UPDATE_TEST",
            description="Original"
        )
        created = await role_service.create(role_data)
        
        update_data = RoleUpdate(
            name="Updated Name",
            description="Updated description"
        )
        updated = await role_service.update(created.id, update_data)
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.code == "UPDATE_TEST"  # Code should not change
    
    async def test_update_role_duplicate_name(self, db_session, role_service: RoleService):
        """Test updating role to duplicate name raises 409."""
        # Create first role
        role1_data = RoleCreate(name="Role 1", code="ROLE1")
        await role_service.create(role1_data)
        
        # Create second role
        role2_data = RoleCreate(name="Role 2", code="ROLE2")
        role2 = await role_service.create(role2_data)
        
        # Try to update role2 with role1's name
        update_data = RoleUpdate(name="Role 1")
        
        with pytest.raises(HTTPException) as exc_info:
            await role_service.update(role2.id, update_data)
        
        assert exc_info.value.status_code == 409
    
    async def test_delete_custom_role(self, db_session, role_service: RoleService):
        """Test deleting a custom (non-system) role."""
        role_data = RoleCreate(
            name="Custom Role",
            code="CUSTOM",
            description="Can be deleted"
        )
        created = await role_service.create(role_data)
        
        result = await role_service.delete(created.id)
        
        assert result == True
        
        # Verify soft delete
        deleted = await role_service.get_by_id(created.id)
        assert deleted is None  # Should not be found without include_deleted
        
        deleted_with_flag = await role_service.get_by_id(created.id, include_deleted=True)
        assert deleted_with_flag is not None
        assert deleted_with_flag.is_deleted == True
    
    async def test_delete_system_role_fails(self, db_session, role_service: RoleService):
        """Test deleting a system role raises 409."""
        # Create a system role directly (bypassing service validation)
        system_role = Role(
            name="Admin",
            code="ADMIN",
            is_system_role=True
        )
        db_session.add(system_role)
        await db_session.commit()
        await db_session.refresh(system_role)
        
        with pytest.raises(HTTPException) as exc_info:
            await role_service.delete(system_role.id)
        
        assert exc_info.value.status_code == 409
        assert "system" in exc_info.value.detail.lower()
    
    async def test_get_list(self, db_session, role_service: RoleService):
        """Test getting paginated list of roles."""
        # Create multiple roles
        for i in range(5):
            role_data = RoleCreate(
                name=f"Role {i}",
                code=f"ROLE{i}",
                description=f"Role number {i}"
            )
            await role_service.create(role_data)
        
        # Get first page
        pagination = PaginationParams(page=1, page_size=3)
        result = await role_service.get_list(pagination=pagination)
        
        assert result.total >= 5
        assert len(result.data) == 3
        assert result.page == 1
        assert result.page_size == 3
    
    async def test_get_list_filter_system_role(self, db_session, role_service: RoleService):
        """Test filtering roles by is_system_role."""
        # Create custom role
        await role_service.create(RoleCreate(name="Custom", code="CUSTOM"))
        
        # Create system role
        system_role = Role(name="System", code="SYSTEM", is_system_role=True)
        db_session.add(system_role)
        await db_session.commit()
        
        # Filter for system roles only
        pagination = PaginationParams(page=1, page_size=10)
        result = await role_service.get_list(
            pagination=pagination,
            filters={"is_system_role": True}
        )
        
        assert all(role.is_system_role for role in result.data)
