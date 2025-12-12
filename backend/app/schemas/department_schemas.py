"""
Department schemas for API request/response models.
"""
from typing import Optional, List
from datetime import date
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


class ManagerSummary(BaseSchema):
    """Minimal manager information for department display purposes only"""
    id: UUID = Field(..., description="Manager employee ID")
    first_name: str = Field(..., description="Manager first name")
    last_name: str = Field(..., description="Manager last name")


class DepartmentSummary(BaseSchema):
    """Minimal department information for relationship display"""
    id: UUID = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code")


class DepartmentCreate(CreateSchema):
    name: str = Field(..., description="Department name", min_length=1, max_length=200)
    code: str = Field(..., description="Unique department code", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="Department description")
    parent_id: Optional[UUID] = Field(None, description="Parent department ID")
    manager_id: Optional[UUID] = Field(None, description="Manager employee ID")
    is_active: bool = Field(True, description="Whether the department is active")

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Department code cannot be empty')
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Department name cannot be empty')
        return v.strip()


class DepartmentUpdate(UpdateSchema):
    name: Optional[str] = Field(None, description="Department name", min_length=1, max_length=200)
    code: Optional[str] = Field(None, description="Unique department code", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="Department description")
    parent_id: Optional[UUID] = Field(None, description="Parent department ID")
    manager_id: Optional[UUID] = Field(None, description="Manager employee ID")
    is_active: Optional[bool] = Field(None, description="Whether the department is active")

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError('Department code cannot be empty')
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError('Department name cannot be empty')
        return v.strip()


class DepartmentResponse(ResponseSchema):
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Unique department code")
    description: Optional[str] = Field(None, description="Department description")
    parent_id: Optional[UUID] = Field(None, description="Parent department ID")
    parent: Optional[DepartmentSummary] = Field(None, description="Parent department details")
    manager_id: Optional[UUID] = Field(None, description="Manager employee ID")
    manager: Optional[ManagerSummary] = Field(None, description="Manager details (null if manager is inactive, deleted, or not assigned)")
    is_active: bool = Field(..., description="Active status")
    children: Optional[List[DepartmentSummary]] = Field(default=None, description="List of child departments (shallow)")


class DepartmentListResponse(ListResponseSchema[DepartmentResponse]):
    pass


class PositionSummary(ResponseSchema):
    """Position information for employee display"""
    id: UUID = Field(..., description="Position ID")
    name: str = Field(..., description="Position name")


class DepartmentEmployeeResponse(ResponseSchema):
    """Employee information for department employee list"""
    id: UUID = Field(..., description="Employee ID")
    employee_number: str = Field(..., description="Employee number")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    email: str = Field(..., description="Employee email")
    position: Optional[PositionSummary] = Field(None, description="Employee position")
    hire_date: Optional[date] = Field(None, description="Employee hire date")
