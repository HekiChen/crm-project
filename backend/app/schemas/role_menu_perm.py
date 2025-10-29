"""
RoleMenuPerm schemas for API requests and responses.
"""
from typing import List
from uuid import UUID

from pydantic import Field

from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema


class RoleMenuPermCreate(CreateSchema):
    """Schema for creating a role-menu permission."""
    role_id: UUID = Field(..., description="Role ID")
    menu_id: UUID = Field(..., description="Menu ID")
    can_read: bool = Field(default=True, description="Permission to read/view")
    can_write: bool = Field(default=False, description="Permission to create/update")
    can_delete: bool = Field(default=False, description="Permission to delete")


class RoleMenuPermBatchCreate(CreateSchema):
    """Schema for batch creating role-menu permissions."""
    role_id: UUID = Field(..., description="Role ID")
    permissions: List[dict] = Field(
        ..., 
        description="List of menu permissions",
        example=[
            {"menu_id": "uuid-1", "can_read": True, "can_write": False, "can_delete": False},
            {"menu_id": "uuid-2", "can_read": True, "can_write": True, "can_delete": False}
        ]
    )


class RoleMenuPermUpdate(UpdateSchema):
    """Schema for updating a role-menu permission."""
    can_read: bool | None = None
    can_write: bool | None = None
    can_delete: bool | None = None


class RoleMenuPermResponse(ResponseSchema):
    """Schema for role-menu permission response."""
    role_id: UUID
    menu_id: UUID
    can_read: bool
    can_write: bool
    can_delete: bool
