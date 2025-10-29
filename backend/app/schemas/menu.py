"""
Menu schemas for API requests and responses.
"""
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


class MenuCreate(CreateSchema):
    """Schema for creating a menu."""
    name: str = Field(..., min_length=1, max_length=100, description="Menu item name")
    path: str = Field(..., min_length=1, max_length=255, description="URL path or route")
    icon: Optional[str] = Field(None, max_length=100, description="Icon identifier")
    parent_id: Optional[UUID] = Field(None, description="Parent menu ID for hierarchy")
    sort_order: int = Field(default=0, description="Display order (lower = higher priority)")
    menu_type: str = Field(default="frontend", description="Menu type: frontend, backend, or api")
    is_active: bool = Field(default=True, description="Whether menu is active")
    
    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: str) -> str:
        """Validate menu_type is one of allowed values."""
        allowed = {"frontend", "backend", "api"}
        if v not in allowed:
            raise ValueError(f"menu_type must be one of {allowed}")
        return v


class MenuUpdate(UpdateSchema):
    """Schema for updating a menu."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    path: Optional[str] = Field(None, min_length=1, max_length=255)
    icon: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    menu_type: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate menu_type is one of allowed values."""
        if v is not None:
            allowed = {"frontend", "backend", "api"}
            if v not in allowed:
                raise ValueError(f"menu_type must be one of {allowed}")
        return v


class MenuResponse(ResponseSchema):
    """Schema for menu response."""
    name: str
    path: str
    icon: Optional[str]
    parent_id: Optional[UUID]
    sort_order: int
    menu_type: str
    is_active: bool


class MenuListResponse(ListResponseSchema):
    """Schema for paginated menu list response."""
    data: list[MenuResponse]


class MenuTree(ResponseSchema):
    """Schema for menu tree structure with nested children."""
    name: str
    path: str
    icon: Optional[str]
    sort_order: int
    menu_type: str
    is_active: bool
    children: list["MenuTree"] = Field(default_factory=list, description="Child menus")
