"""Work log API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_employee
from app.models.employee import Employee
from app.schemas.work_log import (
    WorkLogCreate,
    WorkLogUpdate,
    WorkLogResponse,
    WorkLogListResponse,
    WorkLogFilter,
    RateWorkLogRequest,
    LogType,
)
from app.services.work_log_service import WorkLogService


router = APIRouter()


@router.post("/", response_model=WorkLogResponse, status_code=status.HTTP_201_CREATED)
async def create_work_log(
    work_log_in: WorkLogCreate,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogResponse:
    """
    Create a new work log for the current user.
    
    The end_date will be automatically calculated based on log_type:
    - daily: same as start_date
    - weekly: start_date + 6 days
    - monthly: last day of the month
    - yearly: December 31 of the year
    """
    service = WorkLogService(db)
    return await service.create_work_log(
        employee_id=current_employee.id,
        work_log_in=work_log_in,
        current_user_id=current_employee.id,
    )


@router.get("/", response_model=WorkLogListResponse)
async def list_work_logs(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID (requires authorization)"),
    log_type: Optional[LogType] = Query(None, description="Filter by log type"),
    start_date_from: Optional[str] = Query(None, description="Filter logs from this date (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Filter logs to this date (YYYY-MM-DD)"),
    rated: Optional[bool] = Query(None, description="Filter by rated status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogListResponse:
    """
    List work logs with filters.
    
    By default, returns only the current user's work logs.
    To view another employee's logs, you must be their direct manager.
    """
    from datetime import date as date_type
    
    # Parse dates
    start_date_from_parsed = date_type.fromisoformat(start_date_from) if start_date_from else None
    start_date_to_parsed = date_type.fromisoformat(start_date_to) if start_date_to else None
    
    filters = WorkLogFilter(
        employee_id=employee_id,
        log_type=log_type,
        start_date_from=start_date_from_parsed,
        start_date_to=start_date_to_parsed,
        rated=rated,
        page=page,
        page_size=page_size,
    )
    
    service = WorkLogService(db)
    return await service.list_work_logs(filters, current_employee.id)


@router.get("/team", response_model=WorkLogListResponse)
async def list_team_work_logs(
    log_type: Optional[LogType] = Query(None, description="Filter by log type"),
    start_date_from: Optional[str] = Query(None, description="Filter logs from this date (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Filter logs to this date (YYYY-MM-DD)"),
    rated: Optional[bool] = Query(None, description="Filter by rated status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogListResponse:
    """
    List work logs of all direct reports (manager view).
    
    Returns work logs created by employees who report directly to the current user.
    """
    from datetime import date as date_type
    
    # Parse dates
    start_date_from_parsed = date_type.fromisoformat(start_date_from) if start_date_from else None
    start_date_to_parsed = date_type.fromisoformat(start_date_to) if start_date_to else None
    
    filters = WorkLogFilter(
        log_type=log_type,
        start_date_from=start_date_from_parsed,
        start_date_to=start_date_to_parsed,
        rated=rated,
        page=page,
        page_size=page_size,
    )
    
    service = WorkLogService(db)
    return await service.get_team_work_logs(current_employee.id, filters)


@router.get("/{work_log_id}", response_model=WorkLogResponse)
async def get_work_log(
    work_log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogResponse:
    """
    Get a specific work log by ID.
    
    You can view your own work logs or those of your direct reports.
    """
    service = WorkLogService(db)
    return await service.get_work_log(work_log_id, current_employee.id)


@router.put("/{work_log_id}", response_model=WorkLogResponse)
async def update_work_log(
    work_log_id: UUID,
    work_log_update: WorkLogUpdate,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogResponse:
    """
    Update a work log.
    
    You can only update your own work logs, and only before they have been rated.
    Cannot change log_type or dates after creation.
    """
    service = WorkLogService(db)
    return await service.update_work_log(
        work_log_id=work_log_id,
        work_log_update=work_log_update,
        current_user_id=current_employee.id,
    )


@router.delete("/{work_log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_log(
    work_log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> None:
    """
    Delete a work log (soft delete).
    
    You can only delete your own work logs.
    """
    service = WorkLogService(db)
    await service.delete_work_log(work_log_id, current_employee.id)


@router.post("/{work_log_id}/rate", response_model=WorkLogResponse)
async def rate_work_log(
    work_log_id: UUID,
    rate_request: RateWorkLogRequest,
    db: AsyncSession = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee),
) -> WorkLogResponse:
    """
    Rate a work log (manager only).
    
    Only the direct manager of the employee who created the work log can rate it.
    Rating must be between 1 and 5 stars.
    """
    service = WorkLogService(db)
    return await service.rate_work_log(
        work_log_id=work_log_id,
        rating=rate_request.rating,
        current_user_id=current_employee.id,
    )
