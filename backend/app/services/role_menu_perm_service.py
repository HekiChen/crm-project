"""
RoleMenuPerm service for managing role-menu permissions.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.role_menu_perm import RoleMenuPerm
from app.models.role import Role
from app.models.menu import Menu
from app.schemas.role_menu_perm import (
    RoleMenuPermCreate,
    RoleMenuPermUpdate,
    RoleMenuPermResponse,
)
from app.schemas.base import PaginationParams
from app.services.base import BaseService


class RoleMenuPermService(BaseService[RoleMenuPerm, RoleMenuPermCreate, RoleMenuPermUpdate, RoleMenuPermResponse]):
    """Service for role-menu permission management."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(RoleMenuPerm, db, RoleMenuPermResponse)
    
    async def get_by_id(
        self,
        id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Optional[RoleMenuPerm]:
        """
        Get permission by ID with noload for relationships.
        
        Args:
            id: Permission ID
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Permission if found, None otherwise
        """
        stmt = (
            select(RoleMenuPerm)
            .where(RoleMenuPerm.id == id)
            .options(noload(RoleMenuPerm.role), noload(RoleMenuPerm.menu))
        )
        if not include_deleted:
            stmt = stmt.where(RoleMenuPerm.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_role_and_menu(
        self,
        role_id: UUID,
        menu_id: UUID,
    ) -> Optional[RoleMenuPerm]:
        """
        Get permission by role and menu IDs.
        
        Args:
            role_id: Role ID
            menu_id: Menu ID
            
        Returns:
            Permission if found, None otherwise
        """
        stmt = (
            select(RoleMenuPerm)
            .where(
                RoleMenuPerm.role_id == role_id,
                RoleMenuPerm.menu_id == menu_id,
                RoleMenuPerm.is_deleted == False
            )
            .options(noload(RoleMenuPerm.role), noload(RoleMenuPerm.menu))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(
        self,
        obj_in: RoleMenuPermCreate,
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> RoleMenuPerm:
        """
        Create new role-menu permission with validation.
        
        Args:
            obj_in: Permission creation data
            created_by_id: ID of user creating the permission
            commit: Whether to commit the transaction
            
        Returns:
            Created permission
            
        Raises:
            HTTPException: If role or menu not found, or permission already exists
        """
        # Validate role exists
        role_stmt = select(Role).where(Role.id == obj_in.role_id, Role.is_deleted == False)
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{obj_in.role_id}' not found"
            )
        
        # Validate menu exists
        menu_stmt = select(Menu).where(Menu.id == obj_in.menu_id, Menu.is_deleted == False)
        menu_result = await self.db.execute(menu_stmt)
        menu = menu_result.scalar_one_or_none()
        if not menu:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Menu with id '{obj_in.menu_id}' not found"
            )
        
        # Check for existing permission
        existing = await self.get_by_role_and_menu(obj_in.role_id, obj_in.menu_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Permission for role '{obj_in.role_id}' and menu '{obj_in.menu_id}' already exists"
            )
        
        # Create permission
        obj_data = obj_in.model_dump(exclude_unset=True)
        if created_by_id:
            obj_data["created_by_id"] = created_by_id
        
        perm = RoleMenuPerm(**obj_data)
        self.db.add(perm)
        
        if commit:
            await self.db.commit()
            # Re-query to get clean instance
            perm = await self.get_by_id(perm.id)
        
        return perm
    
    async def batch_create(
        self,
        role_id: UUID,
        permissions_data: List[Dict[str, Any]],
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> List[RoleMenuPerm]:
        """
        Create multiple permissions for a role in batch.
        
        Args:
            role_id: Role ID
            permissions_data: List of permission dicts with menu_id and permission flags
            created_by_id: ID of user creating permissions
            commit: Whether to commit the transaction
            
        Returns:
            List of created permissions
            
        Raises:
            HTTPException: If validation fails
        """
        # Validate role exists
        role_stmt = select(Role).where(Role.id == role_id, Role.is_deleted == False)
        role_result = await self.db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with id '{role_id}' not found"
            )
        
        created_perms = []
        
        for perm_data in permissions_data:
            menu_id_raw = perm_data.get("menu_id")
            if not menu_id_raw:
                continue
            
            # Convert menu_id to UUID if it's a string
            if isinstance(menu_id_raw, str):
                try:
                    from uuid import UUID as UUIDType
                    menu_id = UUIDType(menu_id_raw)
                except ValueError:
                    # Skip invalid UUIDs
                    continue
            else:
                menu_id = menu_id_raw
            
            # Check if permission already exists
            existing = await self.get_by_role_and_menu(role_id, menu_id)
            if existing:
                # Skip existing permissions
                continue
            
            # Validate menu exists
            menu_stmt = select(Menu).where(Menu.id == menu_id, Menu.is_deleted == False)
            menu_result = await self.db.execute(menu_stmt)
            menu = menu_result.scalar_one_or_none()
            if not menu:
                # Skip invalid menus
                continue
            
            # Create permission
            perm_dict = {
                "role_id": role_id,
                "menu_id": menu_id,
                "can_read": perm_data.get("can_read", True),
                "can_write": perm_data.get("can_write", False),
                "can_delete": perm_data.get("can_delete", False),
            }
            if created_by_id:
                perm_dict["created_by_id"] = created_by_id
            
            perm = RoleMenuPerm(**perm_dict)
            self.db.add(perm)
            created_perms.append(perm)
        
        if commit and created_perms:
            await self.db.commit()
            # Re-query to get clean instances
            result = []
            for perm in created_perms:
                refreshed = await self.get_by_id(perm.id)
                if refreshed:
                    result.append(refreshed)
            return result
        
        return created_perms
    
    async def update(
        self,
        id: UUID,
        obj_in: RoleMenuPermUpdate,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Optional[RoleMenuPerm]:
        """
        Update permission.
        
        Args:
            id: Permission ID
            obj_in: Update data
            updated_by_id: ID of user updating the permission
            commit: Whether to commit the transaction
            
        Returns:
            Updated permission if found
        """
        perm = await self.get_by_id(id)
        if not perm:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Update fields
        if updated_by_id:
            update_data["updated_by_id"] = updated_by_id
        
        for field, value in update_data.items():
            if hasattr(perm, field):
                setattr(perm, field, value)
        
        if commit:
            await self.db.commit()
            # Re-query to get clean instance
            perm = await self.get_by_id(id)
        
        return perm
    
    async def update_by_role_and_menu(
        self,
        role_id: UUID,
        menu_id: UUID,
        obj_in: RoleMenuPermUpdate,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Optional[RoleMenuPerm]:
        """
        Update permission by role and menu IDs.
        
        Args:
            role_id: Role ID
            menu_id: Menu ID
            obj_in: Update data
            updated_by_id: ID of user updating the permission
            commit: Whether to commit the transaction
            
        Returns:
            Updated permission if found
        """
        perm = await self.get_by_role_and_menu(role_id, menu_id)
        if not perm:
            return None
        
        return await self.update(perm.id, obj_in, updated_by_id=updated_by_id, commit=commit)
    
    async def delete_by_role_and_menu(
        self,
        role_id: UUID,
        menu_id: UUID,
        *,
        deleted_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> bool:
        """
        Delete permission by role and menu IDs.
        
        Args:
            role_id: Role ID
            menu_id: Menu ID
            deleted_by_id: ID of user deleting the permission
            commit: Whether to commit the transaction
            
        Returns:
            True if deleted, False if not found
        """
        perm = await self.get_by_role_and_menu(role_id, menu_id)
        if not perm:
            return False
        
        return await self.delete(perm.id, deleted_by_id=deleted_by_id, commit=commit)
    
    async def get_by_role(self, role_id: UUID) -> List[RoleMenuPerm]:
        """
        Get all permissions for a role.
        
        Args:
            role_id: Role ID
            
        Returns:
            List of permissions
        """
        stmt = (
            select(RoleMenuPerm)
            .where(RoleMenuPerm.role_id == role_id, RoleMenuPerm.is_deleted == False)
            .options(noload(RoleMenuPerm.role), noload(RoleMenuPerm.menu))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_menu(self, menu_id: UUID) -> List[RoleMenuPerm]:
        """
        Get all permissions for a menu.
        
        Args:
            menu_id: Menu ID
            
        Returns:
            List of permissions
        """
        stmt = (
            select(RoleMenuPerm)
            .where(RoleMenuPerm.menu_id == menu_id, RoleMenuPerm.is_deleted == False)
            .options(noload(RoleMenuPerm.role), noload(RoleMenuPerm.menu))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
