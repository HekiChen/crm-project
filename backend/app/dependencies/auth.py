"""
Authentication dependencies for protected routes.
"""
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.employee import Employee
from app.utils.jwt import decode_token

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_employee(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Employee:
    """
    Get current authenticated employee from JWT token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Employee: Authenticated employee object with roles eagerly loaded
        
    Raises:
        HTTPException: If token is invalid, expired, or employee not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Extract employee ID from token
        employee_id_str: str | None = payload.get("sub")
        if not employee_id_str:
            raise credentials_exception
            
        try:
            employee_id = UUID(employee_id_str)
        except ValueError:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Query employee with roles eagerly loaded
    stmt = (
        select(Employee)
        .options(selectinload(Employee.employee_roles))
        .where(Employee.id == employee_id)
    )
    result = await db.execute(stmt)
    employee = result.scalar_one_or_none()
    
    if employee is None:
        raise credentials_exception
    
    if not employee.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
    
    return employee
