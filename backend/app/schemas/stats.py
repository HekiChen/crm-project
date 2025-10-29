"""
Statistics response schemas.

Defines Pydantic models for dashboard statistics API responses.
"""
from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """
    Dashboard statistics response model.
    
    Contains aggregate counts for key system metrics displayed on the dashboard.
    """
    
    total_employees: int = Field(
        ...,
        description="Total count of non-deleted employees in the system",
        ge=0,
        example=42
    )
    
    total_departments: int = Field(
        ...,
        description="Total count of non-deleted departments in the system",
        ge=0,
        example=8
    )
    
    total_roles: int = Field(
        ...,
        description="Total count of non-deleted roles in the system",
        ge=0,
        example=5
    )
    
    recent_activities: int = Field(
        ...,
        description="Count of work log entries from the last 7 days",
        ge=0,
        example=156
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "total_employees": 42,
                "total_departments": 8,
                "total_roles": 5,
                "recent_activities": 156
            }
        }
