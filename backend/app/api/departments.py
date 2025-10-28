"""
Department API endpoints.
"""
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
)
from app.schemas.base import PaginationParams, MessageResponse
from app.services.department_service import DepartmentService


router = APIRouter(tags=["departments"])


def get_department_service(db: AsyncSession = Depends(get_db)) -> DepartmentService:
    return DepartmentService(db)


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
) -> Any:
    dept = await service.create(dept_in)
    resp = DepartmentResponse.model_validate(dept)
    # Don't populate children on create (new departments have no children yet)
    resp.children = []
    return resp


@router.get("/{id}", response_model=DepartmentResponse)
async def get_department(id: UUID, service: DepartmentService = Depends(get_department_service)) -> Any:
    dept = await service.get_by_id(id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    # populate children IDs shallowly
    children = await service.get_children(id)
    resp = DepartmentResponse.model_validate(dept)
    resp.children = [c.id for c in children]
    return resp


@router.get("/", response_model=DepartmentListResponse)
async def list_departments(pagination: PaginationParams = Depends(), service: DepartmentService = Depends(get_department_service)) -> Any:
    result = await service.get_list(pagination=pagination)
    return result


@router.patch("/{id}", response_model=DepartmentResponse)
async def update_department(id: UUID, dept_in: DepartmentUpdate, service: DepartmentService = Depends(get_department_service)) -> Any:
    dept = await service.update(id, dept_in)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    resp = DepartmentResponse.model_validate(dept)
    # Optionally populate children after update
    children = await service.get_children(id)
    resp.children = [c.id for c in children]
    return resp


@router.delete("/{id}", response_model=MessageResponse)
async def delete_department(id: UUID, service: DepartmentService = Depends(get_department_service)) -> Any:
    success = await service.delete(id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return MessageResponse(message="Department deleted", detail={"id": str(id)})


@router.get("/{id}/children", response_model=List[DepartmentResponse])
async def get_children(id: UUID, service: DepartmentService = Depends(get_department_service)) -> Any:
    children = await service.get_children(id)
    return [DepartmentResponse.model_validate(c) for c in children]


@router.get("/{id}/parent", response_model=DepartmentResponse)
async def get_parent(id: UUID, service: DepartmentService = Depends(get_department_service)) -> Any:
    parent = await service.get_parent(id)
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent not found")
    return DepartmentResponse.model_validate(parent)
