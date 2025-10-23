"""
Centralized error handler middleware for consistent error responses.
"""
from datetime import datetime
from typing import Optional, List

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.logging import get_request_id, log_security_event


class ErrorDetail(BaseModel):
    """Detailed error information for a specific field or issue."""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    request_id: Optional[str] = None
    timestamp: datetime


# Custom exception classes

class AppException(Exception):
    """Base exception for application errors."""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[ErrorDetail]] = None,
    ):
        """
        Initialize application exception.
        
        Args:
            message: Error message
            code: Error code
            status_code: HTTP status code
            details: Optional detailed error information
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class ValidationException(AppException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundException(AppException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None,
    ):
        if resource:
            message = f"{resource} not found"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PermissionDeniedException(AppException):
    """Exception for permission/authorization errors."""
    
    def __init__(
        self,
        message: str = "Permission denied",
    ):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class AuthenticationException(AppException):
    """Exception for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ConflictException(AppException):
    """Exception for resource conflict errors."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class DatabaseException(AppException):
    """Exception for database errors."""
    
    def __init__(
        self,
        message: str = "Database error",
    ):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Error response builders

def build_error_response(
    code: str,
    message: str,
    request_id: Optional[str] = None,
    details: Optional[List[ErrorDetail]] = None,
) -> dict:
    """
    Build standardized error response.
    
    Args:
        code: Error code
        message: Error message
        request_id: Optional request ID
        details: Optional error details
    
    Returns:
        Error response dictionary
    """
    error_response = ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=request_id,
        timestamp=datetime.utcnow(),
    )
    
    # Convert to dict with mode='json' to serialize datetime properly
    return {"error": error_response.model_dump(mode='json')}


def build_validation_error_details(errors: List[dict]) -> List[ErrorDetail]:
    """
    Build error details from Pydantic validation errors.
    
    Args:
        errors: List of Pydantic validation errors
    
    Returns:
        List of ErrorDetail objects
    """
    details = []
    
    for error in errors:
        # Get field path
        loc = error.get("loc", ())
        field = ".".join(str(x) for x in loc if x != "body")
        
        # Get error message and type
        msg = error.get("msg", "Validation error")
        error_type = error.get("type", "value_error")
        
        details.append(ErrorDetail(
            field=field if field else None,
            message=msg,
            type=error_type,
        ))
    
    return details


# Exception handlers

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle custom application exceptions.
    
    Args:
        request: FastAPI request
        exc: Application exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Log security events for certain error types
    if isinstance(exc, (AuthenticationException, PermissionDeniedException)):
        log_security_event(
            request_id=request_id or "unknown",
            event=f"{exc.code}: {exc.message}",
            severity="medium",
            path=request.url.path,
            method=request.method,
        )
    
    response = build_error_response(
        code=exc.code,
        message=exc.message,
        request_id=request_id,
        details=exc.details,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.
    
    Args:
        request: FastAPI request
        exc: HTTP exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Map status codes to error codes
    status_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    
    code = status_to_code.get(exc.status_code, "HTTP_ERROR")
    
    # Log security events for auth errors
    if exc.status_code in [401, 403]:
        log_security_event(
            request_id=request_id or "unknown",
            event=f"HTTP {exc.status_code}: {exc.detail}",
            severity="medium",
            path=request.url.path,
        )
    
    response = build_error_response(
        code=code,
        message=str(exc.detail),
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle FastAPI request validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Build error details
    details = build_validation_error_details(exc.errors())
    
    response = build_error_response(
        code="VALIDATION_ERROR",
        message="Invalid input data",
        request_id=request_id,
        details=details,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response,
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: PydanticValidationError,
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: Pydantic validation error
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Build error details
    details = build_validation_error_details(exc.errors())
    
    response = build_error_response(
        code="VALIDATION_ERROR",
        message="Validation error",
        request_id=request_id,
        details=details,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response,
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    """
    Handle SQLAlchemy integrity errors (unique constraints, foreign keys, etc.).
    
    Args:
        request: FastAPI request
        exc: Integrity error
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Extract useful information from the error
    # Check both the main exception message and orig if available
    error_msg = str(exc)
    if hasattr(exc, "orig") and exc.orig:
        error_msg += " " + str(exc.orig)
    
    error_msg_upper = error_msg.upper()
    error_msg_lower = error_msg.lower()
    
    # Determine specific type of integrity error
    if "UNIQUE" in error_msg_upper or "duplicate" in error_msg_lower:
        message = "A record with this value already exists"
        code = "DUPLICATE_RESOURCE"
    elif "FOREIGN KEY" in error_msg_upper or "foreign" in error_msg_lower:
        message = "Invalid reference to related resource"
        code = "INVALID_REFERENCE"
    elif "NOT NULL" in error_msg_upper or "null" in error_msg_lower:
        message = "Required field cannot be null"
        code = "NULL_CONSTRAINT_VIOLATION"
    else:
        message = "Database integrity constraint violated"
        code = "INTEGRITY_ERROR"
    
    response = build_error_response(
        code=code,
        message=message,
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response,
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle generic SQLAlchemy errors.
    
    Args:
        request: FastAPI request
        exc: SQLAlchemy error
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Log the detailed error
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Database error: {exc}", exc_info=True)
    
    response = build_error_response(
        code="DATABASE_ERROR",
        message="A database error occurred",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle any unhandled exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception
    
    Returns:
        JSON error response
    """
    request_id = get_request_id(request)
    
    # Log the detailed error
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Log as security event (potential issue)
    log_security_event(
        request_id=request_id or "unknown",
        event=f"Unhandled exception: {type(exc).__name__}",
        severity="high",
        path=request.url.path,
        error_type=type(exc).__name__,
    )
    
    response = build_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(ValidationException, app_exception_handler)
    app.add_exception_handler(NotFoundException, app_exception_handler)
    app.add_exception_handler(PermissionDeniedException, app_exception_handler)
    app.add_exception_handler(AuthenticationException, app_exception_handler)
    app.add_exception_handler(ConflictException, app_exception_handler)
    app.add_exception_handler(DatabaseException, app_exception_handler)
    
    # Starlette/FastAPI exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_exception_handler)
    
    # Database exceptions
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
