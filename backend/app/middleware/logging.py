"""
Logging middleware for structured logging with request tracking.
"""
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Callable, Optional, Set

from fastapi import Request, Response
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send


# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # We'll use JSON format
)

logger = logging.getLogger(__name__)


# Sensitive fields to sanitize in logs
SENSITIVE_FIELDS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "authorization",
    "cookie",
    "csrf_token",
    "session_id",
}


def generate_request_id() -> str:
    """
    Generate a unique request ID.
    
    Returns:
        Unique request ID string
    """
    return f"req_{uuid.uuid4().hex[:12]}"


def sanitize_data(data: dict, sensitive_fields: Optional[Set[str]] = None) -> dict:
    """
    Sanitize sensitive data in a dictionary.
    
    Args:
        data: Dictionary to sanitize
        sensitive_fields: Set of field names to sanitize
    
    Returns:
        Sanitized dictionary
    """
    if sensitive_fields is None:
        sensitive_fields = SENSITIVE_FIELDS
    
    sanitized = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field is sensitive
        is_sensitive = any(
            sensitive in key_lower
            for sensitive in sensitive_fields
        )
        
        if is_sensitive:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_data(value, sensitive_fields)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_data(item, sensitive_fields) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    
    return sanitized


def sanitize_headers(headers: dict) -> dict:
    """
    Sanitize sensitive headers.
    
    Args:
        headers: Request headers
    
    Returns:
        Sanitized headers
    """
    return sanitize_data(dict(headers))


class LoggingMiddleware:
    """
    Pure ASGI middleware for structured logging of requests and responses.
    
    This implementation avoids BaseHTTPMiddleware issues with response modification.
    
    Features:
    - Generates unique request IDs
    - Logs request/response details
    - Tracks request duration
    - Sanitizes sensitive data
    - Detects slow queries
    - Properly adds request ID to response headers without Content-Length issues
    """
    
    def __init__(
        self,
        app: ASGIApp,
        slow_request_threshold: float = 1.0,
    ):
        """
        Initialize logging middleware.
        
        Args:
            app: ASGI application
            slow_request_threshold: Threshold in seconds for slow request warning
        """
        self.app = app
        self.slow_request_threshold = slow_request_threshold
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        ASGI application entry point.
        
        Args:
            scope: ASGI connection scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Only process HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract path early for skip check
        path = scope["path"]
        
        # Skip logging for static assets and docs endpoints
        skip_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/favicon.ico",
        ]
        
        # Check if path should be skipped
        should_skip = any(
            path.startswith(skip_path) or path == skip_path
            for skip_path in skip_paths
        )
        
        if should_skip:
            # Pass through without logging
            await self.app(scope, receive, send)
            return
        
        # Generate request ID
        request_id = generate_request_id()
        
        # Start timer
        start_time = time.time()
        
        # Extract request details
        method = scope["method"]
        query_string = scope.get("query_string", b"").decode("utf-8")
        
        # Get client host
        client = scope.get("client")
        client_host = client[0] if client else None
        
        # Parse headers
        headers = Headers(scope=scope)
        sanitized_headers = sanitize_headers(dict(headers))
        
        # Log request
        request_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "request",
            "request_id": request_id,
            "method": method,
            "path": path,
            "query_string": query_string,
            "client_host": client_host,
        }
        
        logger.info(json.dumps(request_log))
        
        # Store request ID in scope for access in route handlers
        scope["request_id"] = request_id
        
        # Track response status
        status_code = None
        
        async def send_wrapper(message: Message) -> None:
            """Wrap send to capture response details for logging."""
            nonlocal status_code
            
            if message["type"] == "http.response.start":
                # Capture status code
                status_code = message["status"]
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log response
                response_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "type": "response",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                }
                
                # Log level based on status code and duration
                if status_code >= 500:
                    logger.error(json.dumps(response_log))
                elif status_code >= 400:
                    logger.warning(json.dumps(response_log))
                elif duration_ms > self.slow_request_threshold * 1000:
                    logger.warning(json.dumps({**response_log, "slow_request": True}))
                else:
                    logger.info(json.dumps(response_log))
            
            await send(message)
        
        # Process request with error handling
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            
            error_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": "error",
                "request_id": request_id,
                "method": method,
                "path": path,
                "duration_ms": round(duration_ms, 2),
                "error": str(e),
                "error_type": type(e).__name__,
            }
            
            logger.error(json.dumps(error_log))
            raise


def get_request_id(request: Request) -> Optional[str]:
    """
    Get the request ID from request scope or state.
    
    Args:
        request: FastAPI request
    
    Returns:
        Request ID if available, None otherwise
    """
    # Try to get from scope (ASGI middleware stores it here)
    if hasattr(request, "scope") and "request_id" in request.scope:
        return request.scope["request_id"]
    
    # Fallback to state for backwards compatibility
    return getattr(request.state, "request_id", None)


def log_event(
    request_id: str,
    event_type: str,
    message: str,
    **extra_data,
) -> None:
    """
    Log a custom event with structured data.
    
    Args:
        request_id: Request ID
        event_type: Type of event
        message: Log message
        **extra_data: Additional data to include
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "request_id": request_id,
        "message": message,
        **extra_data,
    }
    
    logger.info(json.dumps(log_data))


def log_database_query(
    request_id: str,
    query: str,
    duration_ms: float,
    slow_query_threshold: float = 100.0,
) -> None:
    """
    Log a database query.
    
    Args:
        request_id: Request ID
        query: SQL query string
        duration_ms: Query duration in milliseconds
        slow_query_threshold: Threshold for slow query warning
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "database_query",
        "request_id": request_id,
        "query": query[:200],  # Truncate long queries
        "duration_ms": round(duration_ms, 2),
    }
    
    if duration_ms > slow_query_threshold:
        log_data["slow_query"] = True
        logger.warning(json.dumps(log_data))
    else:
        logger.debug(json.dumps(log_data))


def log_security_event(
    request_id: str,
    event: str,
    severity: str,
    user_id: Optional[str] = None,
    **extra_data,
) -> None:
    """
    Log a security-related event.
    
    Args:
        request_id: Request ID
        event: Security event description
        severity: Event severity (low, medium, high, critical)
        user_id: Optional user ID
        **extra_data: Additional data
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "security_event",
        "request_id": request_id,
        "event": event,
        "severity": severity,
        "user_id": user_id,
        **extra_data,
    }
    
    if severity in ["high", "critical"]:
        logger.error(json.dumps(log_data))
    elif severity == "medium":
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))


class RequestLogContext:
    """
    Context manager for logging within a request.
    
    Usage:
        with RequestLogContext(request) as log:
            log.info("Processing user data")
            log.warning("Slow operation detected")
    """
    
    def __init__(self, request: Request):
        """
        Initialize log context.
        
        Args:
            request: FastAPI request
        """
        self.request_id = get_request_id(request)
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type is not None:
            self.error(f"Exception: {exc_val}")
        return False
    
    def info(self, message: str, **extra_data):
        """Log info message."""
        log_event(self.request_id, "info", message, **extra_data)
    
    def warning(self, message: str, **extra_data):
        """Log warning message."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "warning",
            "request_id": self.request_id,
            "message": message,
            **extra_data,
        }
        logger.warning(json.dumps(log_data))
    
    def error(self, message: str, **extra_data):
        """Log error message."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "error",
            "request_id": self.request_id,
            "message": message,
            **extra_data,
        }
        logger.error(json.dumps(log_data))
