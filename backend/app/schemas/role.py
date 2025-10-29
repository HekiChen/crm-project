"""
Role schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


class RoleCreate(CreateSchema):
    """Schema for creating a new role."""
    name: str = Field(..., min_length=1, max_length=100, description="Role name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique role code")
    description: Optional[str] = Field(None, max_length=500, description="Role description")


class RoleUpdate(UpdateSchema):
    """Schema for updating an existing role."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    # Note: code is intentionally excluded - it's immutable after creation


class RoleResponse(ResponseSchema):
    """Schema for role response."""
    name: str = Field(..., description="Role name")
    code: str = Field(..., description="Unique role code")
    description: Optional[str] = Field(None, description="Role description")
    is_system_role: bool = Field(..., description="Whether this is a system role")


class RoleListResponse(ListResponseSchema[RoleResponse]):
    """Schema for paginated role list response."""
    pass

