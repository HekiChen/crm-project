"""
Authentication middleware for JWT token validation and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Set
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()

# Token blacklist (in-memory for now, should be Redis in production)
token_blacklist: Set[str] = set()


class TokenData(BaseModel):
    """Token payload data."""
    user_id: UUID
    username: str
    exp: datetime


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    """Current authenticated user."""
    id: UUID
    username: str
    email: str
    is_active: bool = True
    is_superuser: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    user_id: UUID,
    username: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User ID
        username: Username
        expires_delta: Optional expiration time delta
    
    Returns:
        JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
        "type": "access",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def create_refresh_token(
    user_id: UUID,
    username: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        user_id: User ID
        username: Username
        expires_delta: Optional expiration time delta
    
    Returns:
        JWT refresh token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "sub": str(user_id),
        "username": username,
        "exp": expire,
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def create_token_pair(user_id: UUID, username: str) -> TokenPair:
    """
    Create both access and refresh tokens.
    
    Args:
        user_id: User ID
        username: Username
    
    Returns:
        TokenPair with access and refresh tokens
    """
    access_token = create_access_token(user_id, username)
    refresh_token = create_refresh_token(user_id, username)
    
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token
    
    Returns:
        TokenData with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        user_id_str: str = payload.get("sub")
        username: str = payload.get("username")
        exp_timestamp: int = payload.get("exp")
        
        if user_id_str is None or username is None:
            raise credentials_exception
        
        # Convert to proper types
        user_id = UUID(user_id_str)
        exp = datetime.fromtimestamp(exp_timestamp)
        
        return TokenData(user_id=user_id, username=username, exp=exp)
    
    except JWTError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception


def blacklist_token(token: str) -> None:
    """
    Add a token to the blacklist.
    
    Args:
        token: JWT token to blacklist
    """
    token_blacklist.add(token)


def is_token_blacklisted(token: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token: JWT token to check
    
    Returns:
        True if blacklisted, False otherwise
    """
    return token in token_blacklist


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Get the current authenticated user from JWT token.
    
    This is a FastAPI dependency that can be used in route handlers.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
    
    Returns:
        CurrentUser with user information
    
    Raises:
        HTTPException: If token is invalid, expired, or blacklisted
    
    Usage:
        @router.get("/me")
        async def get_me(current_user: CurrentUser = Depends(get_current_user)):
            return current_user
    """
    token = credentials.credentials
    
    # Check if token is blacklisted
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    token_data = decode_token(token)
    
    # In a real application, you would fetch the user from the database here
    # For now, we'll return the user data from the token
    # NOTE: This is where you would integrate with your User model
    user = CurrentUser(
        id=token_data.user_id,
        username=token_data.username,
        email=f"{token_data.username}@example.com",  # Placeholder
        is_active=True,
        is_superuser=False,
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    return user


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Get the current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        CurrentUser if active
    
    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Get the current superuser.
    
    Args:
        current_user: Current user from get_current_user dependency
    
    Returns:
        CurrentUser if superuser
    
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


class OptionalAuth:
    """
    Optional authentication dependency.
    
    Returns user if authenticated, None if not.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    
    async def __call__(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
    ) -> Optional[CurrentUser]:
        """
        Get current user if authenticated, None otherwise.
        
        Args:
            credentials: Optional HTTP Bearer credentials
        
        Returns:
            CurrentUser if authenticated, None otherwise
        """
        if credentials is None:
            return None
        
        try:
            token = credentials.credentials
            
            # Check if token is blacklisted
            if is_token_blacklisted(token):
                return None
            
            # Decode token
            token_data = decode_token(token)
            
            # Return user
            return CurrentUser(
                id=token_data.user_id,
                username=token_data.username,
                email=f"{token_data.username}@example.com",
                is_active=True,
                is_superuser=False,
            )
        except HTTPException:
            return None


# Public routes that don't require authentication
PUBLIC_ROUTES = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}


def is_public_route(path: str) -> bool:
    """
    Check if a route is public (doesn't require authentication).
    
    Args:
        path: Request path
    
    Returns:
        True if public route, False otherwise
    """
    return path in PUBLIC_ROUTES or path.startswith("/static/")
