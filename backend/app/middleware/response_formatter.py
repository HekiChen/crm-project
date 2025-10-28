"""
Response formatter middleware for consistent API response structure.

Pure ASGI implementation to avoid BaseHTTPMiddleware Content-Length issues.
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.middleware.logging import get_request_id


class ResponseFormatterMiddleware:
    """
    Pure ASGI middleware to format all successful responses with consistent structure.
    
    Wraps response data with metadata including request_id and timestamp.
    Handles both single entity and paginated list responses.
    
    This implementation avoids BaseHTTPMiddleware to prevent Content-Length issues
    when modifying response bodies.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize response formatter middleware.
        
        Args:
            app: ASGI application
        """
        self.app = app
    
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
        
        # Extract request details
        path = scope["path"]
        
        # Skip formatting for documentation endpoints
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/static", "/favicon.ico"]
        if any(path.startswith(skip_path) or path == skip_path for skip_path in skip_paths):
            await self.app(scope, receive, send)
            return
        
        # Get request ID from scope (set by LoggingMiddleware)
        request_id = scope.get("request_id")
        
        # Track response details
        status_code = None
        response_headers = []
        response_body = []
        start_sent = False  # Track if we've sent http.response.start
        
        async def send_wrapper(message: Message) -> None:
            """Wrap send to capture and modify response."""
            nonlocal status_code, response_headers, response_body, start_sent
            
            if message["type"] == "http.response.start":
                # Capture status code and headers
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
                
                # Check if we should format this response
                if not self._should_format_response(status_code, response_headers):
                    # Pass through without modification
                    await send(message)
                    start_sent = True
                    return
                
                # Store headers, but don't send yet (we need to modify the body first)
                # We'll send both start and body together after formatting
                
            elif message["type"] == "http.response.body":
                # Capture body chunks
                body_chunk = message.get("body", b"")
                if body_chunk:
                    response_body.append(body_chunk)
                
                # Check if this is the last chunk
                more_body = message.get("more_body", False)
                
                if not more_body:
                    # All body received, now format and send
                    if self._should_format_response(status_code, response_headers) and status_code is not None:
                        # Format the response (status_code is guaranteed non-None here)
                        formatted_body = await self._format_response(
                            response_body,
                            status_code,
                            response_headers,
                            request_id,
                        )
                        
                        if formatted_body is not None:
                            # Update headers with new content length
                            new_headers = [
                                (name, value)
                                for name, value in response_headers
                                if name.lower() not in {b"content-length", b"content-type"}
                            ]
                            new_headers.append((b"content-type", b"application/json"))
                            new_headers.append((b"content-length", str(len(formatted_body)).encode()))
                            
                            # Send modified response
                            await send({
                                "type": "http.response.start",
                                "status": status_code,
                                "headers": new_headers,
                            })
                            await send({
                                "type": "http.response.body",
                                "body": formatted_body,
                                "more_body": False,
                            })
                            return
                    
                    # If we get here, pass through original response
                    if response_body:
                        # Send headers first if not sent yet
                        if not start_sent and status_code is not None and response_headers:
                            await send({
                                "type": "http.response.start",
                                "status": status_code,
                                "headers": response_headers,
                            })
                            start_sent = True
                        
                        # Send body
                        await send({
                            "type": "http.response.body",
                            "body": b"".join(response_body),
                            "more_body": False,
                        })
                    else:
                        await send(message)
                else:
                    # More body coming, don't send yet
                    pass
            else:
                await send(message)
        
        # Process request
        await self.app(scope, receive, send_wrapper)
    
    def _should_format_response(
        self,
        status_code: Optional[int],
        headers: list,
    ) -> bool:
        """
        Determine if response should be formatted.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
        
        Returns:
            True if response should be formatted
        """
        if status_code is None:
            return False
        
        # Only format successful responses (2xx)
        if status_code < 200 or status_code >= 300:
            return False
        
        # Skip 204 No Content
        if status_code == 204:
            return False
        
        # Only format JSON responses
        content_type = None
        for name, value in headers:
            if name.lower() == b"content-type":
                content_type = value.decode("utf-8", errors="ignore")
                break
        
        if not content_type or "application/json" not in content_type:
            return False
        
        return True
    
    async def _format_response(
        self,
        body_chunks: list,
        status_code: int,
        headers: list,
        request_id: Optional[str],
    ) -> Optional[bytes]:
        """
        Format response body with metadata wrapper.
        
        Args:
            body_chunks: List of body chunks
            status_code: HTTP status code
            headers: Response headers
            request_id: Request ID
        
        Returns:
            Formatted response body or None if formatting fails
        """
        # Combine body chunks
        body = b"".join(body_chunks)
        
        if not body:
            return None
        
        # Parse JSON
        try:
            data = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not valid JSON, skip formatting
            return None
        
        # Check if already formatted
        if self._is_already_formatted(data):
            return None
        
        # Check if error response
        if "error" in data:
            # Don't format error responses
            return None
        
        # Format the response
        formatted_data = self._wrap_response(data, request_id)
        
        # Convert back to JSON bytes
        return json.dumps(formatted_data).encode("utf-8")
    
    def _is_already_formatted(self, data: Any) -> bool:
        """
        Check if data is already in our formatted structure.
        
        Args:
            data: Response data
        
        Returns:
            True if already formatted
        """
        if not isinstance(data, dict):
            return False
        
        # Check if has both "data" and "meta" keys
        return "data" in data and "meta" in data
    
    def _wrap_response(
        self,
        data: Any,
        request_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Wrap response data with metadata.
        
        Args:
            data: Original response data
            request_id: Request ID
        
        Returns:
            Wrapped response with data and meta
        """
        # Check if this is a paginated response
        if self._is_paginated_response(data):
            return self._format_paginated_response(data, request_id)
        
        # Standard single entity or list response
        return {
            "data": data,
            "meta": {
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }
    
    def _is_paginated_response(self, data: Any) -> bool:
        """
        Check if response data is a paginated list response.
        
        Args:
            data: Response data
        
        Returns:
            True if paginated response
        """
        if not isinstance(data, dict):
            return False
        
        # Check for pagination fields from ListResponseSchema
        required_fields = {"items", "total", "page", "page_size"}
        return required_fields.issubset(data.keys())
    
    def _format_paginated_response(
        self,
        data: Dict[str, Any],
        request_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Format paginated list response.
        
        Args:
            data: Paginated response data with items, total, page, page_size
            request_id: Request ID
        
        Returns:
            Formatted paginated response
        """
        items = data.get("items", [])
        total = data.get("total", 0)
        page = data.get("page", 1)
        page_size = data.get("page_size", 20)
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        # Calculate has_next and has_previous
        has_next = page < total_pages
        has_previous = page > 1
        
        return {
            "data": items,
            "meta": {
                "page": page,
                "page_size": page_size,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
                "request_id": request_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        }


def format_response(
    data: Any,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Helper function to manually format a response.
    
    Args:
        data: Response data
        request_id: Optional request ID
    
    Returns:
        Formatted response dictionary
    """
    return {
        "data": data,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }


def format_paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 20,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Helper function to manually format a paginated response.
    
    Args:
        items: List of items
        total: Total count of items
        page: Current page number
        page_size: Items per page
        request_id: Optional request ID
    
    Returns:
        Formatted paginated response dictionary
    """
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    # Calculate has_next and has_previous
    has_next = page < total_pages
    has_previous = page > 1
    
    return {
        "data": items,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }
