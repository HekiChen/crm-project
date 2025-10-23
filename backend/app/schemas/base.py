"""
Base Pydantic schema classes for API request/response models.
"""
from datetime import datetime
from typing import Generic, TypeVar, Optional, Any
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class BaseSchema(PydanticBaseModel):
    """
    Base schema with common configuration.
    
    All schemas should inherit from this to ensure consistent behavior.
    """
    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM model conversion
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class CreateSchema(BaseSchema):
    """
    Base schema for create operations.
    
    Excludes auto-generated fields like id, timestamps, and audit fields.
    Entity-specific create schemas should inherit from this.
    """
    pass


class UpdateSchema(BaseSchema):
    """
    Base schema for update operations.
    
    All fields are optional by default for PATCH operations.
    Entity-specific update schemas should inherit from this and
    make fields Optional[T].
    """
    pass


class ResponseSchema(BaseSchema):
    """
    Base schema for API responses.
    
    Includes all system-managed fields (id, timestamps, audit).
    """
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_deleted: bool = Field(default=False, description="Soft delete flag")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    created_by_id: Optional[UUID] = Field(None, description="Creator user ID")
    updated_by_id: Optional[UUID] = Field(None, description="Last updater user ID")


class IDResponse(BaseSchema):
    """
    Simple response schema containing only an ID.
    
    Useful for operations that only need to return the created/updated ID.
    """
    id: UUID = Field(..., description="Record identifier")


T = TypeVar("T", bound=BaseSchema)


class ListResponseSchema(BaseSchema, Generic[T]):
    """
    Generic schema for paginated list responses.
    
    Includes data array and pagination metadata.
    
    Example:
        ```python
        class UserListResponse(ListResponseSchema[UserResponse]):
            pass
        ```
    """
    data: list[T] = Field(default_factory=list, description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_previous: bool = Field(..., description="Whether previous page exists")
    
    @classmethod
    def create(
        cls,
        data: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "ListResponseSchema[T]":
        """
        Create a list response with calculated pagination metadata.
        
        Args:
            data: List of items for current page
            total: Total number of items across all pages
            page: Current page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            ListResponseSchema instance with pagination metadata
        """
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class PaginationParams(BaseSchema):
    """
    Schema for pagination query parameters.
    
    Use as a dependency in FastAPI endpoints:
        ```python
        @router.get("/users")
        async def list_users(pagination: PaginationParams = Depends()):
            skip = (pagination.page - 1) * pagination.page_size
            ...
        ```
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Field name to sort by"
    )
    sort_order: Optional[str] = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'"
    )
    
    @property
    def skip(self) -> int:
        """Calculate the number of records to skip for pagination."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias for page_size for clarity in some contexts."""
        return self.page_size


class MessageResponse(BaseSchema):
    """
    Simple message response schema.
    
    Useful for operations that return a success/info message.
    """
    message: str = Field(..., description="Response message")
    detail: Optional[dict[str, Any]] = Field(
        None,
        description="Additional details"
    )


class ErrorDetail(BaseSchema):
    """
    Schema for error details in error responses.
    """
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseSchema):
    """
    Standardized error response schema.
    
    Used by error handler middleware for consistent error formatting.
    """
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[list[ErrorDetail]] = Field(
        None,
        description="Detailed error information"
    )
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
