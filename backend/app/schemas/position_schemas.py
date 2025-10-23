"""
Position schemas for API request/response models.
"""
from typing import Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema, ListResponseSchema


class PositionCreate(CreateSchema):
    """
    Schema for creating a new position.
    
    Used in POST /positions requests.
    """
    name: str = Field(..., description="Position name (e.g., 'Software Engineer', 'Manager')", min_length=1, max_length=200)
    code: str = Field(..., description="Unique position code (e.g., 'SE-001', 'MGR-001')", min_length=1, max_length=50)
    level: Optional[int] = Field(None, description="Position level in organizational hierarchy (1-10)", ge=1, le=10)
    description: Optional[str] = Field(None, description="Detailed description of the position and responsibilities")
    department_id: Optional[UUID] = Field(None, description="Department ID (when Department entity exists)")
    is_active: bool = Field(True, description="Whether position is active and available for assignment")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate position code format."""
        if not v:
            raise ValueError('Position code cannot be empty')
        # Code should be alphanumeric with optional hyphens/underscores
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Position code must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate position name."""
        if not v or not v.strip():
            raise ValueError('Position name cannot be empty')
        return v.strip()


class PositionUpdate(UpdateSchema):
    """
    Schema for updating a position.
    
    All fields are optional for PATCH /positions/{id} requests.
    """
    name: Optional[str] = Field(None, description="Position name", min_length=1, max_length=200)
    code: Optional[str] = Field(None, description="Unique position code", min_length=1, max_length=50)
    level: Optional[int] = Field(None, description="Position level (1-10)", ge=1, le=10)
    description: Optional[str] = Field(None, description="Position description")
    department_id: Optional[UUID] = Field(None, description="Department ID")
    is_active: Optional[bool] = Field(None, description="Active status")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate position code format."""
        if v is None:
            return v
        if not v:
            raise ValueError('Position code cannot be empty')
        if not all(c.isalnum() or c in '-_' for c in v):
            raise ValueError('Position code must contain only alphanumeric characters, hyphens, and underscores')
        return v.upper()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate position name."""
        if v is not None and (not v or not v.strip()):
            raise ValueError('Position name cannot be empty')
        return v.strip() if v else v


class PositionResponse(ResponseSchema):
    """
    Schema for position responses.
    
    Includes all fields including system-managed fields (id, timestamps, audit).
    Used in API responses for GET, POST, PUT, PATCH endpoints.
    """
    name: str = Field(..., description="Position name")
    code: str = Field(..., description="Unique position code")
    level: Optional[int] = Field(None, description="Position level (1-10)")
    description: Optional[str] = Field(None, description="Position description")
    department_id: Optional[UUID] = Field(None, description="Department ID")
    is_active: bool = Field(..., description="Active status")


class PositionListResponse(ListResponseSchema[PositionResponse]):
    """
    Schema for paginated position list responses.
    
    Used in GET /positions responses.
    """
    pass
