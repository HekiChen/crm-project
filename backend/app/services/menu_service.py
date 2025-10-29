"""
Menu service for CRUD operations and hierarchy management.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload

from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse, MenuTree, MenuListResponse
from app.schemas.base import PaginationParams
from app.services.base import BaseService


class MenuService(BaseService[Menu, MenuCreate, MenuUpdate, MenuResponse]):
    """Service for menu management with hierarchy support."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Menu, db, MenuResponse)
    
    async def get_by_id(
        self,
        id: UUID,
        *,
        include_deleted: bool = False
    ) -> Optional[Menu]:
        """
        Get menu by ID with noload for relationships.
        
        Args:
            id: Menu ID
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Menu if found, None otherwise
        """
        stmt = (
            select(Menu)
            .where(Menu.id == id)
            .options(noload(Menu.parent), noload(Menu.children), noload(Menu.role_permissions))
        )
        if not include_deleted:
            stmt = stmt.where(Menu.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_path(self, path: str) -> Optional[Menu]:
        """
        Get menu by path.
        
        Args:
            path: Menu path
            
        Returns:
            Menu if found, None otherwise
        """
        stmt = (
            select(Menu)
            .where(Menu.path == path, Menu.is_deleted == False)
            .options(noload(Menu.parent), noload(Menu.children), noload(Menu.role_permissions))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _check_circular_reference(self, menu_id: UUID, parent_id: UUID) -> bool:
        """
        Check if setting parent_id would create a circular reference.
        
        Args:
            menu_id: Current menu ID
            parent_id: Proposed parent ID
            
        Returns:
            True if circular reference detected
        """
        visited = set()
        current_id = parent_id
        
        while current_id:
            if current_id == menu_id:
                return True
            
            if current_id in visited:
                # Circular reference in existing data
                return True
            
            visited.add(current_id)
            
            # Get parent of current
            stmt = select(Menu.parent_id).where(Menu.id == current_id, Menu.is_deleted == False)
            result = await self.db.execute(stmt)
            current_id = result.scalar_one_or_none()
        
        return False
    
    async def create(
        self,
        obj_in: MenuCreate,
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Menu:
        """
        Create new menu with validation.
        
        Args:
            obj_in: Menu creation data
            created_by_id: ID of user creating the menu
            commit: Whether to commit the transaction
            
        Returns:
            Created menu
            
        Raises:
            HTTPException: If path already exists or circular reference detected
        """
        # Check for duplicate path
        existing = await self.get_by_path(obj_in.path)
        if existing:
            raise HTTPException(status_code=409, detail=f"Menu with path '{obj_in.path}' already exists")
        
        # Check for circular reference if parent_id provided
        if obj_in.parent_id:
            parent = await self.get_by_id(obj_in.parent_id)
            if not parent:
                raise HTTPException(status_code=404, detail=f"Parent menu with id '{obj_in.parent_id}' not found")
        
        # Create menu
        obj_data = obj_in.model_dump(exclude_unset=True)
        if created_by_id:
            obj_data["created_by_id"] = created_by_id
        
        menu = Menu(**obj_data)
        self.db.add(menu)
        
        if commit:
            await self.db.commit()
            # Re-query to get clean instance
            menu = await self.get_by_id(menu.id)
        
        return menu
    
    async def update(
        self,
        id: UUID,
        obj_in: MenuUpdate,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Optional[Menu]:
        """
        Update menu with validation.
        
        Args:
            id: Menu ID
            obj_in: Update data
            updated_by_id: ID of user updating the menu
            commit: Whether to commit the transaction
            
        Returns:
            Updated menu if found
            
        Raises:
            HTTPException: If path conflict or circular reference detected
        """
        menu = await self.get_by_id(id)
        if not menu:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check for path uniqueness if path is being updated
        if "path" in update_data and update_data["path"] != menu.path:
            existing = await self.get_by_path(update_data["path"])
            if existing and existing.id != id:
                raise HTTPException(status_code=409, detail=f"Menu with path '{update_data['path']}' already exists")
        
        # Check for circular reference if parent_id is being updated
        if "parent_id" in update_data and update_data["parent_id"]:
            if update_data["parent_id"] == id:
                raise HTTPException(status_code=409, detail="Menu cannot be its own parent")
            
            is_circular = await self._check_circular_reference(id, update_data["parent_id"])
            if is_circular:
                raise HTTPException(status_code=409, detail="Circular reference detected in menu hierarchy")
            
            # Check parent exists
            parent = await self.get_by_id(update_data["parent_id"])
            if not parent:
                raise HTTPException(status_code=404, detail=f"Parent menu with id '{update_data['parent_id']}' not found")
        
        # Update fields
        if updated_by_id:
            update_data["updated_by_id"] = updated_by_id
        
        for field, value in update_data.items():
            if hasattr(menu, field):
                setattr(menu, field, value)
        
        if commit:
            await self.db.commit()
            # Re-query to get clean instance
            menu = await self.get_by_id(id)
        
        return menu
    
    async def get_list(
        self,
        *,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        include_deleted: bool = False
    ) -> MenuListResponse:
        """
        Get paginated list of menus with optional filters.
        
        Args:
            pagination: Pagination parameters
            filters: Optional filters (parent_id, menu_type, is_active)
            include_deleted: Whether to include soft-deleted records
            
        Returns:
            Paginated list response
        """
        # Build base query
        query = select(Menu)
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(Menu.is_deleted == False)
        
        # Apply filters
        if filters:
            if "parent_id" in filters:
                if filters["parent_id"] is None:
                    query = query.where(Menu.parent_id.is_(None))
                else:
                    query = query.where(Menu.parent_id == filters["parent_id"])
            
            if "menu_type" in filters:
                query = query.where(Menu.menu_type == filters["menu_type"])
            
            if "is_active" in filters:
                query = query.where(Menu.is_active == filters["is_active"])
        
        # Apply noload for relationships
        query = query.options(
            noload(Menu.parent),
            noload(Menu.children),
            noload(Menu.role_permissions)
        )
        
        # Get total count
        count_query = select(func.count()).select_from(Menu)
        if not include_deleted:
            count_query = count_query.where(Menu.is_deleted == False)
        if filters:
            # Apply same filters to count
            if "parent_id" in filters:
                if filters["parent_id"] is None:
                    count_query = count_query.where(Menu.parent_id.is_(None))
                else:
                    count_query = count_query.where(Menu.parent_id == filters["parent_id"])
            if "menu_type" in filters:
                count_query = count_query.where(Menu.menu_type == filters["menu_type"])
            if "is_active" in filters:
                count_query = count_query.where(Menu.is_active == filters["is_active"])
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        if pagination.sort_by and hasattr(Menu, pagination.sort_by):
            sort_column = getattr(Menu, pagination.sort_by)
            if pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by sort_order then name
            query = query.order_by(Menu.sort_order, Menu.name)
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        menus = list(result.scalars().all())
        
        # Convert to response schemas
        items = [MenuResponse.model_validate(menu) for menu in menus]
        
        # Return paginated response
        return MenuListResponse.create(
            data=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    async def get_children(self, parent_id: UUID) -> list[Menu]:
        """
        Get all immediate children of a menu.
        
        Args:
            parent_id: Parent menu ID
            
        Returns:
            List of child menus
        """
        stmt = (
            select(Menu)
            .where(Menu.parent_id == parent_id, Menu.is_deleted == False)
            .order_by(Menu.sort_order, Menu.name)
            .options(noload(Menu.parent), noload(Menu.children), noload(Menu.role_permissions))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_tree(self, parent_id: Optional[UUID] = None) -> list[MenuTree]:
        """
        Get menu hierarchy as tree structure.
        
        Args:
            parent_id: Starting parent ID (None for root menus)
            
        Returns:
            List of MenuTree with nested children
        """
        # Get menus at this level
        stmt = (
            select(Menu)
            .where(Menu.is_deleted == False)
            .order_by(Menu.sort_order, Menu.name)
        )
        
        if parent_id is None:
            stmt = stmt.where(Menu.parent_id.is_(None))
        else:
            stmt = stmt.where(Menu.parent_id == parent_id)
        
        result = await self.db.execute(stmt)
        menus = result.scalars().all()
        
        # Build tree recursively
        tree = []
        for menu in menus:
            # Get children recursively
            children = await self.get_tree(parent_id=menu.id)
            
            menu_dict = {
                "id": menu.id,
                "created_at": menu.created_at,
                "updated_at": menu.updated_at,
                "is_deleted": menu.is_deleted,
                "deleted_at": menu.deleted_at,
                "created_by_id": menu.created_by_id,
                "updated_by_id": menu.updated_by_id,
                "name": menu.name,
                "path": menu.path,
                "icon": menu.icon,
                "sort_order": menu.sort_order,
                "menu_type": menu.menu_type,
                "is_active": menu.is_active,
                "children": children
            }
            tree.append(MenuTree(**menu_dict))
        
        return tree
