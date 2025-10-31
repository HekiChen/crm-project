"""
Role service implementing business rules for RBAC.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, joinedload

from app.models.role import Role
from app.models.employee import Employee
from app.models.employee_role import EmployeeRole
from app.models.role_menu_perm import RoleMenuPerm
from app.models.menu import Menu
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
)
from app.schemas.base import PaginationParams
from app.services.base import BaseService


class RoleService(BaseService[Role, RoleCreate, RoleUpdate, RoleResponse]):
    """Service for role management with RBAC business rules."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Role, db, RoleResponse)

    async def get_by_id(
        self,
        id: UUID,
        *,
        include_deleted: bool = False,
    ) -> Optional[Role]:
        """
        Get role by ID with relationships noload to prevent lazy loading.
        """
        stmt = select(Role).where(Role.id == id).options(
            noload(Role.employee_roles),
            noload(Role.menu_permissions)
        )
        if not include_deleted:
            stmt = stmt.where(Role.is_deleted == False)  # noqa: E712
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Role]:
        """Get role by unique code."""
        stmt = select(Role).where(
            Role.code == code,
            Role.is_deleted == False  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        obj_in: RoleCreate,
        *,
        created_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Role:
        """
        Create a new role with uniqueness validation.
        
        Business Rules:
        - Role name must be unique across active roles
        - Role code must be unique across active roles
        """
        # Check unique name
        stmt = select(Role).where(
            Role.name == obj_in.name,
            Role.is_deleted == False  # noqa: E712
        )
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with name '{obj_in.name}' already exists"
            )

        # Check unique code
        existing = await self.get_by_code(obj_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role with code '{obj_in.code}' already exists"
            )

        # Create the object
        obj_data = obj_in.model_dump(exclude_unset=True)
        if created_by_id:
            obj_data["created_by_id"] = created_by_id
        
        db_obj = Role(**obj_data)
        self.db.add(db_obj)
        
        # Flush to get the role ID before creating permissions
        await self.db.flush()
        
        # Auto-assign permissions for all menus
        stmt = select(Menu).where(Menu.is_deleted == False)  # noqa: E712
        result = await self.db.execute(stmt)
        menus = result.scalars().all()
        
        for menu in menus:
            # For "Roles" menu, set all permissions to False (no access)
            # For other menus, grant read-only access
            is_roles_menu = menu.name == "Roles"
            perm = RoleMenuPerm(
                role_id=db_obj.id,
                menu_id=menu.id,
                can_read=not is_roles_menu,  # False for Roles, True for others
                can_write=False,
                can_delete=False,
                created_by_id=created_by_id
            )
            self.db.add(perm)
        
        if commit:
            await self.db.commit()
            # Re-query with noload to prevent lazy loading during serialization
            db_obj = await self.get_by_id(db_obj.id)
        
        return db_obj

    async def update(
        self,
        id: UUID,
        obj_in: RoleUpdate,
        *,
        updated_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> Optional[Role]:
        """
        Update an existing role.
        
        Business Rules:
        - Role name must remain unique across active roles
        - Role code cannot be changed (immutable)
        """
        existing = await self.get_by_id(id)
        if not existing:
            return None

        # If name changes, ensure uniqueness
        if obj_in.name is not None and obj_in.name != existing.name:
            stmt = select(Role).where(
                Role.name == obj_in.name,
                Role.is_deleted == False  # noqa: E712
            )
            result = await self.db.execute(stmt)
            conflict = result.scalar_one_or_none()
            if conflict and conflict.id != id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Role with name '{obj_in.name}' already exists"
                )

        # Update fields
        update_data = obj_in.model_dump(exclude_unset=True)
        if updated_by_id:
            update_data["updated_by_id"] = updated_by_id
        
        for field, value in update_data.items():
            if hasattr(existing, field):
                setattr(existing, field, value)
        
        if commit:
            await self.db.commit()
            # Re-query with noload to prevent lazy loading during serialization
            existing = await self.get_by_id(existing.id)
        
        return existing

    async def delete(
        self,
        id: UUID,
        *,
        deleted_by_id: Optional[UUID] = None,
        commit: bool = True
    ) -> bool:
        """
        Soft-delete a role.
        
        Business Rules:
        - System roles (is_system_role=True) cannot be deleted
        - Deletion cascades to RoleMenuPerm (handled by model)
        """
        existing = await self.get_by_id(id)
        if not existing:
            return False

        # Check if system role
        if existing.is_system_role:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="System roles cannot be deleted"
            )

        # Soft delete
        existing.is_deleted = True
        if deleted_by_id:
            existing.deleted_by_id = deleted_by_id
        
        if commit:
            await self.db.commit()
        
        return True

    async def get_list(
        self,
        *,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
        include_deleted: bool = False,
    ) -> RoleListResponse:
        """
        Get paginated list of roles with optional filtering and search.
        
        Supports filtering by is_system_role via filters dict.
        Supports searching by role name or code.
        """
        # Build base query with noload
        query = select(Role).options(
            noload(Role.employee_roles),
            noload(Role.menu_permissions)
        )
        
        # Apply soft-delete filter
        if not include_deleted:
            query = query.where(Role.is_deleted == False)  # noqa: E712
        
        # Apply search
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Role.name.ilike(search_term),
                    Role.code.ilike(search_term)
                )
            )
        
        # Apply filters
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(Role, field):
                    if isinstance(value, list):
                        conditions.append(getattr(Role, field).in_(value))
                    else:
                        conditions.append(getattr(Role, field) == value)
            
            if conditions:
                query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.db.execute(count_query)
        total = result.scalar() or 0
        
        # Apply sorting
        if pagination.sort_by and hasattr(Role, pagination.sort_by):
            sort_column = getattr(Role, pagination.sort_by)
            if pagination.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by created_at desc
            query = query.order_by(Role.created_at.desc())
        
        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)
        
        # Execute query
        result = await self.db.execute(query)
        db_objects = list(result.scalars().all())
        
        # Convert to response schemas
        response_data = [RoleResponse.model_validate(obj) for obj in db_objects]
        
        # Return paginated response
        return RoleListResponse.create(
            data=response_data,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_permissions(self, role_id: UUID) -> List[RoleMenuPerm]:
        """Get all menu permissions for a role with menu details."""
        role = await self.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        stmt = (
            select(RoleMenuPerm)
            .where(
                RoleMenuPerm.role_id == role_id,
                RoleMenuPerm.is_deleted == False  # noqa: E712
            )
            .options(joinedload(RoleMenuPerm.menu))
        )
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())

    async def get_employees(self, role_id: UUID) -> List[EmployeeRole]:
        """Get all employees assigned to a role with employee details."""
        role = await self.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        stmt = (
            select(EmployeeRole)
            .where(EmployeeRole.role_id == role_id)
            .options(
                joinedload(EmployeeRole.employee).joinedload(Employee.position),
                joinedload(EmployeeRole.employee).joinedload(Employee.department)
            )
        )
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())
