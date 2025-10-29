"""
Authentication schemas for request/response validation.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: EmailStr = Field(..., description="User email address (used as username)")
    password: str = Field(..., min_length=6, description="User password")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "username": "admin@example.com",
                    "password": "password123"
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token (optional)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                }
            ]
        }
    }


class RefreshRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str = Field(..., description="Refresh token to exchange for new access token")


class RoleInfo(BaseModel):
    """Schema for role information in user info response."""
    id: UUID = Field(..., description="Role ID")
    name: str = Field(..., description="Role name")
    code: str = Field(..., description="Role code")
    description: Optional[str] = Field(None, description="Role description")
    
    model_config = {
        "from_attributes": True
    }


class UserInfo(BaseModel):
    """Schema for current user information response."""
    id: UUID = Field(..., description="Employee ID")
    email: str = Field(..., description="Employee email")
    first_name: str = Field(..., description="Employee first name")
    last_name: str = Field(..., description="Employee last name")
    full_name: str = Field(..., description="Employee full name")
    employee_number: str = Field(..., description="Employee number")
    hire_date: date = Field(..., description="Employee hire date")
    is_active: bool = Field(..., description="Whether employee account is active")
    roles: list[RoleInfo] = Field(default=[], description="Assigned roles")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "admin@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "full_name": "John Doe",
                    "employee_number": "EMP001",
                    "hire_date": "2023-01-15",
                    "is_active": True,
                    "roles": [
                        {
                            "id": "456e7890-e89b-12d3-a456-426614174000",
                            "name": "Administrator",
                            "code": "ADMIN",
                            "description": "System administrator role"
                        }
                    ]
                }
            ]
        }
    }
