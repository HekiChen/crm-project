"""
Role API endpoints for RBAC management.
"""
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RoleEmployeeResponse,
)
from app.schemas.role_menu_perm import (
    RoleMenuPermCreate,
    RoleMenuPermBatchCreate,
    RoleMenuPermUpdate,
    RoleMenuPermResponse,
    RoleMenuPermWithMenuResponse,
)
from app.schemas.base import PaginationParams, MessageResponse
from app.services.role_service import RoleService
from app.services.role_menu_perm_service import RoleMenuPermService


router = APIRouter(tags=["roles"])


def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    """Dependency to get role service instance."""
    return RoleService(db)


def get_role_menu_perm_service(db: AsyncSession = Depends(get_db)) -> RoleMenuPermService:
    """Dependency to get role menu permission service instance."""
    return RoleMenuPermService(db)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    service: RoleService = Depends(get_role_service),
) -> Any:
    """Create a new role."""
    role = await service.create(role_in)
    return RoleResponse.model_validate(role)


@router.get("/", response_model=RoleListResponse)
async def list_roles(
    pagination: PaginationParams = Depends(),
    is_system_role: bool = Query(None, description="Filter by system role flag"),
    search: str = Query(None, description="Search by role name or code"),
    service: RoleService = Depends(get_role_service),
) -> Any:
    """Get paginated list of roles with optional filtering."""
    filters = {}
    if is_system_role is not None:
        filters["is_system_role"] = is_system_role
    
    result = await service.get_list(
        pagination=pagination,
        filters=filters if filters else None,
        search=search
    )
    return result


@router.get("/{id}", response_model=RoleResponse)
async def get_role(
    id: UUID,
    service: RoleService = Depends(get_role_service)
) -> Any:
    """Get role by ID."""
    role = await service.get_by_id(id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return RoleResponse.model_validate(role)


@router.patch("/{id}", response_model=RoleResponse)
async def update_role(
    id: UUID,
    role_in: RoleUpdate,
    service: RoleService = Depends(get_role_service)
) -> Any:
    """Update an existing role."""
    role = await service.update(id, role_in)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return RoleResponse.model_validate(role)


@router.delete("/{id}", response_model=MessageResponse)
async def delete_role(
    id: UUID,
    service: RoleService = Depends(get_role_service)
) -> Any:
    """Soft-delete a role (system roles cannot be deleted)."""
    success = await service.delete(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return MessageResponse(
        message="Role deleted successfully",
        detail={"id": str(id)}
    )


@router.get("/{id}/permissions", response_model=List[RoleMenuPermWithMenuResponse])
async def get_role_permissions(
    id: UUID,
    service: RoleService = Depends(get_role_service),
    perm_service: RoleMenuPermService = Depends(get_role_menu_perm_service)
) -> Any:
    """Get all menu permissions for a role with menu details."""
    permissions = await service.get_permissions(id)
    
    # Transform to response schema with menu details
    return [
        RoleMenuPermWithMenuResponse(
            id=perm.id,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
            created_by_id=perm.created_by_id,
            updated_by_id=perm.updated_by_id,
            role_id=perm.role_id,
            menu_id=perm.menu_id,
            menu_name=perm.menu.name,
            menu_path=perm.menu.path,
            menu_type=perm.menu.menu_type,
            menu_icon=perm.menu.icon,
            parent_id=perm.menu.parent_id,
            can_read=perm.can_read,
            can_write=perm.can_write,
            can_delete=perm.can_delete,
        )
        for perm in permissions
    ]


@router.post("/{id}/permissions", response_model=RoleMenuPermResponse, status_code=status.HTTP_201_CREATED)
async def create_role_permission(
    id: UUID,
    perm_in: RoleMenuPermCreate,
    perm_service: RoleMenuPermService = Depends(get_role_menu_perm_service)
) -> Any:
    """Create a single permission for a role."""
    # Ensure role_id matches URL parameter
    if perm_in.role_id != id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role ID in URL must match role_id in request body"
        )
    
    perm = await perm_service.create(perm_in)
    return RoleMenuPermResponse.model_validate(perm)


@router.post("/{id}/permissions/batch", response_model=List[RoleMenuPermResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_role_permissions(
    id: UUID,
    batch_in: RoleMenuPermBatchCreate,
    perm_service: RoleMenuPermService = Depends(get_role_menu_perm_service)
) -> Any:
    """Create multiple permissions for a role in batch."""
    # Ensure role_id matches URL parameter
    if batch_in.role_id != id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role ID in URL must match role_id in request body"
        )
    
    perms = await perm_service.batch_create(id, batch_in.permissions)
    return [RoleMenuPermResponse.model_validate(perm) for perm in perms]


@router.patch("/{id}/permissions/{menu_id}", response_model=RoleMenuPermResponse)
async def update_role_permission(
    id: UUID,
    menu_id: UUID,
    perm_in: RoleMenuPermUpdate,
    perm_service: RoleMenuPermService = Depends(get_role_menu_perm_service)
) -> Any:
    """Update permissions for a specific role-menu binding."""
    perm = await perm_service.update_by_role_and_menu(id, menu_id, perm_in)
    if not perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission for role '{id}' and menu '{menu_id}' not found"
        )
    return RoleMenuPermResponse.model_validate(perm)


@router.delete("/{id}/permissions/{menu_id}", response_model=MessageResponse)
async def delete_role_permission(
    id: UUID,
    menu_id: UUID,
    perm_service: RoleMenuPermService = Depends(get_role_menu_perm_service)
) -> Any:
    """Remove a specific permission from a role."""
    success = await perm_service.delete_by_role_and_menu(id, menu_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission for role '{id}' and menu '{menu_id}' not found"
        )
    return MessageResponse(
        message="Permission deleted successfully",
        detail={"role_id": str(id), "menu_id": str(menu_id)}
    )


@router.get("/{id}/employees", response_model=List[RoleEmployeeResponse])
async def get_role_employees(
    id: UUID,
    service: RoleService = Depends(get_role_service)
) -> Any:
    """Get all employees assigned to this role."""
    employee_roles = await service.get_employees(id)
    
    # Transform to response schema with employee details
    return [
        RoleEmployeeResponse(
            id=er.id,
            created_at=er.assigned_at,
            updated_at=er.assigned_at,
            created_by_id=er.assigned_by_id,
            updated_by_id=er.assigned_by_id,
            employee_id=er.employee_id,
            employee_name=f"{er.employee.first_name} {er.employee.last_name}",
            email=er.employee.email,
            position=er.employee.position.name if er.employee.position else None,
            department=er.employee.department.name if er.employee.department else None,
            assigned_at=er.assigned_at,
            assigned_by_id=er.assigned_by_id,
        )
        for er in employee_roles
    ]
