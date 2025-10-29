"""
JWT token utilities for authentication.

This module provides functions for creating and decoding JWT access and refresh tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: The subject (typically employee ID) to encode in the token
        expires_delta: Optional expiration time delta. If not provided, uses default from settings
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token(subject="123e4567-e89b-12d3-a456-426614174000")
        >>> isinstance(token, str)
        True
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The subject (typically employee ID) to encode in the token
        expires_delta: Optional expiration time delta. If not provided, uses default from settings
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_refresh_token(subject="123e4567-e89b-12d3-a456-426614174000")
        >>> isinstance(token, str)
        True
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)
    
    expire = datetime.now(timezone.utc) + expires_delta
    
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token string to decode
        
    Returns:
        Decoded token payload as a dictionary
        
    Raises:
        JWTError: If the token is invalid, expired, or malformed
        
    Example:
        >>> token = create_access_token("user123")
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user123'
        >>> payload["type"]
        'access'
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Could not validate token: {str(e)}") from e
