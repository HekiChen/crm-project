"""Work log service for business logic and database operations."""

from calendar import monthrange
from datetime import date, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.work_log import WorkLog, LogType
from app.schemas.work_log import (
    WorkLogCreate,
    WorkLogUpdate,
    WorkLogResponse,
    WorkLogListResponse,
    WorkLogFilter,
)


class WorkLogService:
    """
    Service for work log operations.
    
    Provides business logic for work log management including:
    - Creating work logs with auto-calculated end dates
    - Authorization checks (own logs or direct reports only)
    - Manager rating functionality
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize work log service."""
        self.db = db
    
    @staticmethod
    def calculate_end_date(log_type: LogType, start_date: date) -> date:
        """
        Calculate end date based on log type and start date.
        
        - daily: same as start_date
        - weekly: start_date + 6 days
        - monthly: last day of the month
        - yearly: December 31 of the year
        """
        if log_type == LogType.DAILY:
            return start_date
        elif log_type == LogType.WEEKLY:
            return start_date + timedelta(days=6)
        elif log_type == LogType.MONTHLY:
            _, last_day = monthrange(start_date.year, start_date.month)
            return date(start_date.year, start_date.month, last_day)
        elif log_type == LogType.YEARLY:
            return date(start_date.year, 12, 31)
        else:
            raise ValueError(f"Invalid log_type: {log_type}")
    
    async def create_work_log(
        self,
        employee_id: UUID,
        work_log_in: WorkLogCreate,
        current_user_id: UUID,
    ) -> WorkLogResponse:
        """Create a new work log for an employee."""
        # Calculate end date
        end_date = self.calculate_end_date(work_log_in.log_type, work_log_in.start_date)
        
        # Create work log
        work_log = WorkLog(
            employee_id=employee_id,
            log_type=work_log_in.log_type,
            start_date=work_log_in.start_date,
            end_date=end_date,
            progress=work_log_in.progress,
            issues=work_log_in.issues,
            plans=work_log_in.plans,
            created_by_id=current_user_id,
        )
        
        self.db.add(work_log)
        await self.db.commit()
        await self.db.refresh(work_log)
        
        # Load relationships
        result = await self.db.execute(
            select(WorkLog)
            .options(joinedload(WorkLog.employee), joinedload(WorkLog.rated_by))
            .where(WorkLog.id == work_log.id)
        )
        work_log = result.scalar_one()
        
        return WorkLogResponse.model_validate(work_log)
    
    async def can_access_work_log(self, employee_id: UUID, current_user_id: UUID) -> bool:
        """Check if current user can access work logs of the given employee."""
        # User can always access their own logs
        if employee_id == current_user_id:
            return True
        
        # Check if current user is the employee's manager
        result = await self.db.execute(
            select(Employee).where(
                and_(
                    Employee.id == employee_id,
                    Employee.manager_id == current_user_id,
                    Employee.is_deleted == False,
                )
            )
        )
        employee = result.scalar_one_or_none()
        return employee is not None
    
    async def list_work_logs(
        self,
        filters: WorkLogFilter,
        current_user_id: UUID,
    ) -> WorkLogListResponse:
        """List work logs with authorization checks."""
        # Determine which employee's logs to retrieve
        target_employee_id = UUID(filters.employee_id) if filters.employee_id else current_user_id
        
        # Check authorization
        if not await self.can_access_work_log(target_employee_id, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own work logs or those of your direct reports",
            )
        
        # Build query
        query = select(WorkLog).options(
            joinedload(WorkLog.employee),
            joinedload(WorkLog.rated_by)
        ).where(
            and_(
                WorkLog.employee_id == target_employee_id,
                WorkLog.is_deleted == False,
            )
        )
        
        # Apply filters
        if filters.log_type:
            query = query.where(WorkLog.log_type == filters.log_type)
        if filters.start_date_from:
            query = query.where(WorkLog.start_date >= filters.start_date_from)
        if filters.start_date_to:
            query = query.where(WorkLog.start_date <= filters.start_date_to)
        if filters.rated is not None:
            if filters.rated:
                query = query.where(WorkLog.rating.isnot(None))
            else:
                query = query.where(WorkLog.rating.is_(None))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(WorkLog.start_date.desc())
        query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        
        # Execute query
        result = await self.db.execute(query)
        work_logs = result.scalars().unique().all()
        
        return WorkLogListResponse.create(
            data=[WorkLogResponse.model_validate(wl) for wl in work_logs],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )
    
    async def get_team_work_logs(
        self,
        manager_id: UUID,
        filters: WorkLogFilter,
    ) -> WorkLogListResponse:
        """Get work logs of all direct reports."""
        # Build query for team work logs
        query = select(WorkLog).options(
            joinedload(WorkLog.employee),
            joinedload(WorkLog.rated_by)
        ).join(
            Employee, Employee.id == WorkLog.employee_id
        ).where(
            and_(
                Employee.manager_id == manager_id,
                Employee.is_deleted == False,
                WorkLog.is_deleted == False,
            )
        )
        
        # Apply filters
        if filters.log_type:
            query = query.where(WorkLog.log_type == filters.log_type)
        if filters.start_date_from:
            query = query.where(WorkLog.start_date >= filters.start_date_from)
        if filters.start_date_to:
            query = query.where(WorkLog.start_date <= filters.start_date_to)
        if filters.rated is not None:
            if filters.rated:
                query = query.where(WorkLog.rating.isnot(None))
            else:
                query = query.where(WorkLog.rating.is_(None))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination
        query = query.order_by(WorkLog.start_date.desc())
        query = query.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        
        # Execute query
        result = await self.db.execute(query)
        work_logs = result.scalars().unique().all()
        
        return WorkLogListResponse.create(
            data=[WorkLogResponse.model_validate(wl) for wl in work_logs],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )
    
    async def get_work_log(
        self,
        work_log_id: UUID,
        current_user_id: UUID,
    ) -> WorkLogResponse:
        """Get a specific work log by ID."""
        result = await self.db.execute(
            select(WorkLog)
            .options(joinedload(WorkLog.employee), joinedload(WorkLog.rated_by))
            .where(and_(WorkLog.id == work_log_id, WorkLog.is_deleted == False))
        )
        work_log = result.scalar_one_or_none()
        
        if not work_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work log not found",
            )
        
        # Check authorization
        if not await self.can_access_work_log(work_log.employee_id, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own work logs or those of your direct reports",
            )
        
        return WorkLogResponse.model_validate(work_log)
    
    async def update_work_log(
        self,
        work_log_id: UUID,
        work_log_update: WorkLogUpdate,
        current_user_id: UUID,
    ) -> WorkLogResponse:
        """Update a work log (only by the creator, before rating)."""
        result = await self.db.execute(
            select(WorkLog)
            .options(joinedload(WorkLog.employee), joinedload(WorkLog.rated_by))
            .where(and_(WorkLog.id == work_log_id, WorkLog.is_deleted == False))
        )
        work_log = result.scalar_one_or_none()
        
        if not work_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work log not found",
            )
        
        # Only the creator can update
        if work_log.employee_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own work logs",
            )
        
        # Cannot update after being rated
        if work_log.rating is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update work log after it has been rated",
            )
        
        # Apply updates
        update_data = work_log_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(work_log, field, value)
        
        work_log.updated_by_id = current_user_id
        
        await self.db.commit()
        await self.db.refresh(work_log)
        
        return WorkLogResponse.model_validate(work_log)
    
    async def delete_work_log(
        self,
        work_log_id: UUID,
        current_user_id: UUID,
    ) -> None:
        """Soft delete a work log (only by the creator)."""
        result = await self.db.execute(
            select(WorkLog).where(and_(WorkLog.id == work_log_id, WorkLog.is_deleted == False))
        )
        work_log = result.scalar_one_or_none()
        
        if not work_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work log not found",
            )
        
        # Only the creator can delete
        if work_log.employee_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own work logs",
            )
        
        # Soft delete
        work_log.is_deleted = True
        work_log.updated_by_id = current_user_id
        
        await self.db.commit()
    
    async def rate_work_log(
        self,
        work_log_id: UUID,
        rating: int,
        current_user_id: UUID,
    ) -> WorkLogResponse:
        """Rate a work log (only by the employee's manager)."""
        result = await self.db.execute(
            select(WorkLog)
            .options(joinedload(WorkLog.employee), joinedload(WorkLog.rated_by))
            .where(and_(WorkLog.id == work_log_id, WorkLog.is_deleted == False))
        )
        work_log = result.scalar_one_or_none()
        
        if not work_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work log not found",
            )
        
        # Check if current user is the employee's manager
        employee_result = await self.db.execute(
            select(Employee).where(Employee.id == work_log.employee_id)
        )
        employee = employee_result.scalar_one_or_none()
        
        if not employee or employee.manager_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the employee's direct manager can rate work logs",
            )
        
        # Update rating
        work_log.rating = rating
        work_log.rated_by_id = current_user_id
        work_log.rated_at = date.today()
        work_log.updated_by_id = current_user_id
        
        await self.db.commit()
        await self.db.refresh(work_log)
        
        return WorkLogResponse.model_validate(work_log)
