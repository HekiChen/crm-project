"""
Menu API endpoints for navigation structure management.
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.menu import (
    MenuCreate,
    MenuUpdate,
    MenuResponse,
    MenuListResponse,
    MenuTree,
)
from app.schemas.base import PaginationParams
from app.services.menu_service import MenuService

router = APIRouter()


def get_menu_service(db: AsyncSession = Depends(get_db)) -> MenuService:
    """Dependency to get menu service."""
    return MenuService(db)


@router.post("/", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
    menu_in: MenuCreate,
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """
    Create a new menu.
    
    - **name**: Menu item name
    - **path**: URL path or route identifier (must be unique)
    - **icon**: Optional icon identifier
    - **parent_id**: Optional parent menu ID for hierarchy
    - **sort_order**: Display order (default: 0)
    - **menu_type**: frontend, backend, or api (default: frontend)
    - **is_active**: Whether menu is active (default: true)
    """
    menu = await service.create(menu_in)
    return MenuResponse.model_validate(menu)


@router.get("/", response_model=MenuListResponse)
async def list_menus(
    pagination: PaginationParams = Depends(),
    parent_id: Optional[UUID] = Query(None, description="Filter by parent menu ID (null for root menus)"),
    menu_type: Optional[str] = Query(None, description="Filter by menu type (frontend, backend, api)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    service: MenuService = Depends(get_menu_service),
) -> MenuListResponse:
    """
    Get paginated list of menus with optional filters.
    
    Supports filtering by:
    - **parent_id**: Get children of specific parent (or null for root menus)
    - **menu_type**: Filter by type (frontend, backend, api)
    - **is_active**: Filter by active status
    """
    filters = {}
    if parent_id is not None:
        filters["parent_id"] = parent_id
    if menu_type is not None:
        filters["menu_type"] = menu_type
    if is_active is not None:
        filters["is_active"] = is_active
    
    return await service.get_list(pagination=pagination, filters=filters)


@router.get("/tree", response_model=List[MenuTree])
async def get_menu_tree(
    parent_id: Optional[UUID] = Query(None, description="Starting parent ID (null for full tree)"),
    service: MenuService = Depends(get_menu_service),
) -> List[MenuTree]:
    """
    Get menu hierarchy as tree structure.
    
    Returns nested menu tree with all children recursively loaded.
    Useful for rendering navigation menus with hierarchical structure.
    """
    return await service.get_tree(parent_id=parent_id)


@router.get("/{menu_id}", response_model=MenuResponse)
async def get_menu(
    menu_id: UUID,
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """Get menu by ID."""
    menu = await service.get_by_id(menu_id)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    return MenuResponse.model_validate(menu)


@router.patch("/{menu_id}", response_model=MenuResponse)
async def update_menu(
    menu_id: UUID,
    menu_in: MenuUpdate,
    service: MenuService = Depends(get_menu_service),
) -> MenuResponse:
    """
    Update menu by ID.
    
    All fields are optional. Only provided fields will be updated.
    """
    menu = await service.update(menu_id, menu_in)
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    return MenuResponse.model_validate(menu)


@router.delete("/{menu_id}", status_code=status.HTTP_200_OK)
async def delete_menu(
    menu_id: UUID,
    service: MenuService = Depends(get_menu_service),
) -> dict:
    """
    Soft-delete menu by ID.
    
    Menu will be marked as deleted but not removed from database.
    """
    success = await service.delete(menu_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )
    return {"message": "Menu deleted successfully"}


@router.get("/{menu_id}/children", response_model=List[MenuResponse])
async def get_menu_children(
    menu_id: UUID,
    service: MenuService = Depends(get_menu_service),
) -> List[MenuResponse]:
    """
    Get all immediate children of a menu.
    
    Returns only direct children, not the full subtree.
    """
    # First verify parent exists
    parent = await service.get_by_id(menu_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent menu not found"
        )
    
    children = await service.get_children(menu_id)
    return [MenuResponse.model_validate(child) for child in children]
