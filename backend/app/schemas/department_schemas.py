"""
Department schemas for API request/response models.
"""
from typing import Optional, List
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


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
    manager_id: Optional[UUID] = Field(None, description="Manager employee ID")
    is_active: bool = Field(..., description="Active status")
    children: Optional[List[UUID]] = Field(default=None, description="List of child department IDs (shallow)")


class DepartmentListResponse(ListResponseSchema[DepartmentResponse]):
    pass
