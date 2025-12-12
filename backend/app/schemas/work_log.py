"""Work log schemas for API requests and responses."""

from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.models.work_log import LogType
from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


class EmployeeSummary(ResponseSchema):
    """Minimal employee information for work log display."""
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    employee_number: str = Field(..., description="Employee number")


class WorkLogCreate(CreateSchema):
    """
    Schema for creating a new work log.
    
    Used in POST /work-logs requests.
    """
    log_type: LogType = Field(..., description="Type/frequency of work log")
    start_date: date = Field(..., description="Start date of the logging period")
    progress: str = Field(..., min_length=10, description="What was accomplished during this period")
    issues: Optional[str] = Field(None, description="Challenges or blockers encountered")
    plans: Optional[str] = Field(None, description="Plans for the next period")
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: str) -> str:
        """Validate progress field is not empty."""
        if not v or len(v.strip()) < 10:
            raise ValueError('Progress must be at least 10 characters')
        return v.strip()


class WorkLogUpdate(UpdateSchema):
    """
    Schema for updating a work log.
    
    All fields are optional for PATCH /work-logs/{id} requests.
    Cannot update log_type, start_date, or end_date after creation.
    Cannot update if already rated.
    """
    progress: Optional[str] = Field(None, min_length=10, description="What was accomplished during this period")
    issues: Optional[str] = Field(None, description="Challenges or blockers encountered")
    plans: Optional[str] = Field(None, description="Plans for the next period")
    
    @field_validator('progress')
    @classmethod
    def validate_progress(cls, v: Optional[str]) -> Optional[str]:
        """Validate progress field if provided."""
        if v is not None and len(v.strip()) < 10:
            raise ValueError('Progress must be at least 10 characters')
        return v.strip() if v else None


class WorkLogResponse(ResponseSchema):
    """
    Schema for work log responses.
    
    Includes all fields including system-managed fields and relationships.
    Used in API responses for GET, POST, PUT, PATCH endpoints.
    """
    employee_id: UUID = Field(..., description="ID of the employee who created this log")
    log_type: LogType = Field(..., description="Type/frequency of work log")
    start_date: date = Field(..., description="Start date of the logging period")
    end_date: date = Field(..., description="End date of the logging period")
    progress: str = Field(..., description="What was accomplished during this period")
    issues: Optional[str] = Field(None, description="Challenges or blockers encountered")
    plans: Optional[str] = Field(None, description="Plans for the next period")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Manager rating (1-5 stars)")
    rated_by_id: Optional[UUID] = Field(None, description="ID of the manager who rated this log")
    rated_at: Optional[date] = Field(None, description="Date when the log was rated")
    
    # Nested relationships
    employee: Optional[EmployeeSummary] = Field(None, description="Employee who created this log")
    rated_by: Optional[EmployeeSummary] = Field(None, description="Manager who rated this log")


class WorkLogListResponse(ListResponseSchema[WorkLogResponse]):
    """Paginated list of work logs."""
    pass


class WorkLogFilter(CreateSchema):
    """Filter parameters for work log list queries."""
    employee_id: Optional[str] = None
    log_type: Optional[LogType] = None
    start_date_from: Optional[date] = None
    start_date_to: Optional[date] = None
    rated: Optional[bool] = None
    page: int = 1
    page_size: int = 20


class RateWorkLogRequest(CreateSchema):
    """Request schema for rating a work log."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
