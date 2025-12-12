"""
Department API endpoints.
"""
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.department_schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
    DepartmentEmployeeResponse,
    DepartmentSummary,
    ManagerSummary,
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
    
    # Build response with populated relationships
    resp = DepartmentResponse.model_validate(dept)
    
    # Populate manager (use manager_employee relationship from model)
    if dept.manager_employee:
        resp.manager = ManagerSummary(
            id=dept.manager_employee.id,
            first_name=dept.manager_employee.first_name,
            last_name=dept.manager_employee.last_name
        )
    
    # Populate parent
    if dept.parent_id:
        parent = await service.get_by_id(dept.parent_id)
        if parent:
            resp.parent = DepartmentSummary(id=parent.id, name=parent.name, code=parent.code)
    
    # Populate children
    children = await service.get_children(id)
    resp.children = [DepartmentSummary(id=c.id, name=c.name, code=c.code) for c in children]
    
    return resp


@router.get("/", response_model=DepartmentListResponse)
async def list_departments(
    pagination: PaginationParams = Depends(), 
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or code"),
    service: DepartmentService = Depends(get_department_service)
) -> Any:
    """
    Get list of departments with optional filters.
    
    Query Parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10)
    - **search**: Search in name, code, description (optional)
    - **is_active**: Filter by active status (optional, true/false)
    """
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    
    result = await service.get_list(pagination=pagination, filters=filters, search=search)
    return result


@router.patch("/{id}", response_model=DepartmentResponse)
async def update_department(id: UUID, dept_in: DepartmentUpdate, service: DepartmentService = Depends(get_department_service)) -> Any:
    dept = await service.update(id, dept_in)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    
    # Build response with populated relationships
    resp = DepartmentResponse.model_validate(dept)
    
    # Populate manager (use manager_employee relationship from model)
    if dept.manager_employee:
        resp.manager = ManagerSummary(
            id=dept.manager_employee.id,
            first_name=dept.manager_employee.first_name,
            last_name=dept.manager_employee.last_name
        )
    
    # Populate parent
    if dept.parent_id:
        parent = await service.get_by_id(dept.parent_id)
        if parent:
            resp.parent = DepartmentSummary(id=parent.id, name=parent.name, code=parent.code)
    
    # Populate children after update
    children = await service.get_children(id)
    resp.children = [DepartmentSummary(id=c.id, name=c.name, code=c.code) for c in children]
    
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


@router.get("/{id}/employees", response_model=List[DepartmentEmployeeResponse])
async def get_department_employees(
    id: UUID,
    service: DepartmentService = Depends(get_department_service)
) -> Any:
    """Get all employees in a department with position information."""
    employees = await service.get_employees(id)
    return [DepartmentEmployeeResponse.model_validate(emp) for emp in employees]
