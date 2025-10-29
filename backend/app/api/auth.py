"""
Authentication API endpoints.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.dependencies.auth import get_current_employee
from app.models.employee import Employee
from app.models.employee_role import EmployeeRole
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserInfo,
    RoleInfo,
)
from app.utils.auth import verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Authenticate user and return JWT tokens.
    
    - Verify email (username) and password
    - Generate access and refresh tokens
    - Return tokens with expiration info
    
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 403 if account is inactive
    """
    # Find employee by email (case-insensitive)
    stmt = select(Employee).where(Employee.email == request.username.lower())
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    # Check if employee exists and has a password hash
    if not employee or not employee.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(request.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is active
    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Generate tokens with employee ID as subject
    access_token = create_access_token(subject=str(employee.id))
    refresh_token = create_refresh_token(subject=str(employee.id))
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Refresh access token using refresh token.
    
    Validates the refresh token and issues a new access token.
    
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        payload = decode_token(request.refresh_token)
        
        # Verify token type is "refresh"
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract employee ID
        employee_id_str = payload.get("sub")
        if not employee_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Verify employee still exists and is active
        from uuid import UUID
        employee_id = UUID(employee_id_str)
        stmt = select(Employee).where(Employee.id == employee_id)
        result = await db.execute(stmt)
        employee = result.scalar_one_or_none()
        
        if not employee or not employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new access token
        access_token = create_access_token(subject=str(employee.id))
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    current_employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get current authenticated user information with roles.
    
    Returns employee details including assigned roles from the
    employee_roles relationship.
    """
    # Load employee with roles if not already loaded
    stmt = (
        select(Employee)
        .options(selectinload(Employee.employee_roles).selectinload(EmployeeRole.role))
        .where(Employee.id == current_employee.id)
    )
    result = await db.execute(stmt)
    employee = result.scalar_one()
    
    # Build roles list from employee_roles relationship
    roles = [
        RoleInfo(
            id=er.role.id,
            name=er.role.name,
            code=er.role.code,
            description=er.role.description
        )
        for er in employee.employee_roles
    ]
    
    return UserInfo(
        id=employee.id,
        email=employee.email,
        first_name=employee.first_name,
        last_name=employee.last_name,
        full_name=employee.full_name,
        employee_number=employee.employee_number,
        hire_date=employee.hire_date,
        is_active=employee.is_active,
        roles=roles
    )


@router.post("/logout")
async def logout() -> dict[str, str]:
    """
    Logout endpoint (client-side token removal).
    
    Since we're using JWT tokens without a blacklist, logout is handled
    client-side by removing the tokens from storage. This endpoint exists
    for API consistency and future token blacklist implementation.
    """
    return {"message": "Successfully logged out"}
