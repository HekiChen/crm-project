"""
Position API endpoints for job role management.

Provides CRUD operations for Position entities.
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.position import Position
from app.schemas.position_schemas import (
    PositionCreate,
    PositionUpdate,
    PositionResponse,
    PositionListResponse,
)
from app.schemas.base import MessageResponse, PaginationParams
from app.services.position_service import PositionService


router = APIRouter(
    tags=["positions"],
)


def get_position_service(db: AsyncSession = Depends(get_db)) -> PositionService:
    """
    Get position service instance.
    
    Args:
        db: Database session
        
    Returns:
        PositionService instance
    """
    return PositionService(db)


@router.post(
    "/",
    response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create position",
    description="""
Create a new position/job role in the system.

**Requirements:**
- Position code must be unique
- Position name is required
- Level must be between 1-10 if provided

**Example Request:**
```json
{
  "name": "Senior Software Engineer",
  "code": "SSE-001",
  "level": 5,
  "description": "Responsible for designing and implementing complex software systems",
  "is_active": true
}
```

**Returns:**
- 201: Position created successfully
- 409: Position code already exists
- 422: Validation error (invalid data)
    """,
    responses={
        201: {
            "description": "Position created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Senior Software Engineer",
                            "code": "SSE-001",
                            "level": 5,
                            "description": "Responsible for designing and implementing complex software systems",
                            "department_id": None,
                            "is_active": True,
                            "created_at": "2025-10-23T10:00:00Z",
                            "updated_at": "2025-10-23T10:00:00Z",
                            "is_deleted": False
                        }
                    }
                }
            }
        },
        409: {
            "description": "Position code already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Position with code 'SSE-001' already exists"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "code"],
                                "msg": "Position code must contain only alphanumeric characters, hyphens, and underscores",
                                "type": "value_error"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def create_position(
    position_in: PositionCreate,
    service: PositionService = Depends(get_position_service),
) -> Any:
    """
    Create a new position.
    
    Args:
        position_in: Position creation data
        service: Position service
        
    Returns:
        Created position
        
    Raises:
        HTTPException: 409 if position code already exists
    """
    # Service handles duplicate code validation
    position = await service.create(position_in)
    return PositionResponse.model_validate(position)


@router.get(
    "/{id}",
    response_model=PositionResponse,
    summary="Get position by ID",
    description="""
Retrieve a single position by its unique ID.

**Returns:**
- 200: Position found
- 404: Position not found
    """,
    responses={
        200: {
            "description": "Position found",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Senior Software Engineer",
                            "code": "SSE-001",
                            "level": 5,
                            "description": "Responsible for designing and implementing complex software systems",
                            "department_id": None,
                            "is_active": True,
                            "created_at": "2025-10-23T10:00:00Z",
                            "updated_at": "2025-10-23T10:00:00Z",
                            "is_deleted": False
                        }
                    }
                }
            }
        },
        404: {
            "description": "Position not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Position not found"}
                }
            }
        }
    }
)
async def get_position(
    id: UUID,
    service: PositionService = Depends(get_position_service),
) -> Any:
    """
    Get position by ID.
    
    Args:
        id: Position ID
        service: Position service
        
    Returns:
        Position data
        
    Raises:
        HTTPException: 404 if position not found
    """
    position = await service.get_by_id(id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )
    
    return PositionResponse.model_validate(position)


@router.get(
    "/",
    response_model=PositionListResponse,
    summary="List positions",
    description="""
Get a paginated list of positions with optional filters.

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)
- `is_active`: Filter by active status (optional, true/false)

**Example Request:**
```
GET /api/v1/positions?page=1&page_size=10&is_active=true
```

**Returns:**
- 200: Paginated list of positions with metadata
    """,
    responses={
        200: {
            "description": "Successful response with paginated positions",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "name": "Senior Software Engineer",
                                "code": "SSE-001",
                                "level": 5,
                                "description": "Responsible for designing and implementing complex software systems",
                                "department_id": None,
                                "is_active": True,
                                "created_at": "2025-10-23T10:00:00Z",
                                "updated_at": "2025-10-23T10:00:00Z",
                                "is_deleted": False
                            },
                            {
                                "id": "223e4567-e89b-12d3-a456-426614174001",
                                "name": "Project Manager",
                                "code": "PM-001",
                                "level": 6,
                                "description": "Manages project timelines and team coordination",
                                "department_id": None,
                                "is_active": True,
                                "created_at": "2025-10-23T10:05:00Z",
                                "updated_at": "2025-10-23T10:05:00Z",
                                "is_deleted": False
                            }
                        ],
                        "meta": {
                            "page": 1,
                            "page_size": 10,
                            "total": 2,
                            "total_pages": 1,
                            "has_next": False,
                            "has_previous": False
                        }
                    }
                }
            }
        }
    }
)
async def list_positions(
    pagination: PaginationParams = Depends(),
    is_active: bool | None = None,
    service: PositionService = Depends(get_position_service),
) -> Any:
    """
    Get paginated list of positions.
    
    Args:
        pagination: Pagination parameters
        is_active: Filter by active status (optional)
        service: Position service
        
    Returns:
        Paginated list of positions
    """
    # Build filters
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    
    # Get list with filters
    return await service.get_list(pagination=pagination, filters=filters if filters else None)


@router.put(
    "/{id}",
    response_model=PositionResponse,
    summary="Update position",
    description="""
Update all fields of a position.

**Requirements:**
- Position must exist
- Updated code must be unique (if changed)
- All validation rules apply

**Example Request:**
```json
{
  "name": "Lead Software Engineer",
  "code": "LSE-001",
  "level": 6,
  "description": "Leads engineering team and architecture decisions",
  "is_active": true
}
```

**Returns:**
- 200: Position updated successfully
- 404: Position not found
- 409: Updated code conflicts with another position
- 422: Validation error
    """,
    responses={
        200: {
            "description": "Position updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "data": {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "name": "Lead Software Engineer",
                            "code": "LSE-001",
                            "level": 6,
                            "description": "Leads engineering team and architecture decisions",
                            "department_id": None,
                            "is_active": True,
                            "created_at": "2025-10-23T10:00:00Z",
                            "updated_at": "2025-10-23T11:00:00Z",
                            "is_deleted": False
                        }
                    }
                }
            }
        },
        404: {
            "description": "Position not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Position not found"}
                }
            }
        },
        409: {
            "description": "Code conflict",
            "content": {
                "application/json": {
                    "example": {"detail": "Position with code 'LSE-001' already exists"}
                }
            }
        }
    }
)
async def update_position(
    id: UUID,
    position_in: PositionUpdate,
    service: PositionService = Depends(get_position_service),
) -> Any:
    """
    Update position.
    
    Args:
        id: Position ID
        position_in: Position update data
        service: Position service
        
    Returns:
        Updated position
        
    Raises:
        HTTPException: 404 if position not found
        HTTPException: 409 if updated code conflicts with another position
    """
    # Service handles conflict validation
    position = await service.update(id, position_in)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )
    
    return PositionResponse.model_validate(position)


@router.delete(
    "/{id}",
    response_model=MessageResponse,
    summary="Delete position",
    description="""
Soft delete a position.

**Behavior:**
- Position is marked as deleted (soft delete)
- Employees assigned to this position will have their `position_id` set to NULL
- This is handled by the database FK constraint: `ON DELETE SET NULL`
- Position data is retained for audit purposes

**Returns:**
- 200: Position deleted successfully
- 404: Position not found
    """,
    responses={
        200: {
            "description": "Position deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Position deleted successfully"
                    }
                }
            }
        },
        404: {
            "description": "Position not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Position not found"}
                }
            }
        }
    }
)
async def delete_position(
    id: UUID,
    service: PositionService = Depends(get_position_service),
) -> Any:
    """
    Soft delete position.
    
    When a position is deleted, employees assigned to it will have their
    position_id set to NULL due to the ON DELETE SET NULL constraint.
    
    Args:
        id: Position ID
        service: Position service
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if position not found
    """
    success = await service.delete(id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position not found",
        )
    
    return MessageResponse(message="Position deleted successfully")
