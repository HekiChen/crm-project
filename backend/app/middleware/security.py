"""
Security middleware for adding security headers, CORS, and rate limiting.
"""
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from fastapi import Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Adds headers to protect against common web vulnerabilities:
    - HSTS (HTTP Strict Transport Security)
    - X-Frame-Options (Clickjacking protection)
    - X-Content-Type-Options (MIME sniffing protection)
    - X-XSS-Protection (XSS protection)
    - Content-Security-Policy (CSP)
    - Referrer-Policy
    - Permissions-Policy
    """
    
    def __init__(self, app, remove_server_header: bool = True):
        """
        Initialize security headers middleware.
        
        Args:
            app: ASGI application
            remove_server_header: Whether to remove Server header
        """
        super().__init__(app)
        self.remove_server_header = remove_server_header
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Add security headers to response.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain
        
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Check if this is a docs/redoc page - use relaxed CSP for Swagger UI
        is_docs_page = request.url.path in ["/docs", "/redoc", "/openapi.json"]
        
        # Add security headers
        self._add_security_headers(response, is_docs_page=is_docs_page)
        
        # Remove sensitive headers
        if self.remove_server_header:
            self._remove_sensitive_headers(response)
        
        return response
    
    def _add_security_headers(self, response: Response, is_docs_page: bool = False) -> None:
        """
        Add security headers to response.
        
        Args:
            response: Response object
            is_docs_page: Whether this is a docs/redoc page (needs relaxed CSP)
        """
        # HTTP Strict Transport Security
        # Tells browsers to only access the site over HTTPS
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # X-Frame-Options
        # Prevents clickjacking attacks by controlling iframe embedding
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options
        # Prevents MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        # Enable browser XSS protection (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy
        # Defines approved sources of content
        # For docs pages, allow CDN resources needed by Swagger UI/ReDoc
        if is_docs_page:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        
        # Referrer-Policy
        # Controls how much referrer information is sent
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
    
    def _remove_sensitive_headers(self, response: Response) -> None:
        """
        Remove headers that expose server information.
        
        Args:
            response: Response object
        """
        # Remove Server header
        if "server" in response.headers:
            del response.headers["server"]
        
        # Remove X-Powered-By if present
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    Implements a basic token bucket algorithm for rate limiting.
    Note: This is a simple implementation suitable for single-instance deployments.
    For production multi-instance deployments, use Redis-backed rate limiting.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: Optional[int] = None,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: ASGI application
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst size (defaults to requests_per_minute)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size or requests_per_minute
        
        # Token bucket storage: {ip: {"tokens": float, "last_update": float}}
        self._buckets: Dict[str, Dict] = defaultdict(
            lambda: {"tokens": float(self.burst_size), "last_update": time.time()}
        )
        
        # Cleanup old entries periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check rate limit and process request.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/endpoint in chain
        
        Returns:
            Response or rate limit error
        """
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if rate limited
        allowed = self._allow_request(client_ip)
        
        if not allowed:
            response = self._rate_limit_response()
            self._add_rate_limit_headers(response, client_ip)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        self._add_rate_limit_headers(response, client_ip)
        
        # Periodic cleanup
        self._periodic_cleanup()
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: FastAPI request
        
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _allow_request(self, client_ip: str) -> bool:
        """
        Check if request should be allowed based on rate limit.
        
        Uses token bucket algorithm.
        
        Args:
            client_ip: Client IP address
        
        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()
        bucket = self._buckets[client_ip]
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = now - bucket["last_update"]
        tokens_to_add = time_elapsed * (self.requests_per_minute / 60.0)
        
        # Update bucket
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + tokens_to_add
        )
        bucket["last_update"] = now
        
        # Check if request can be allowed
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            return True
        
        return False
    
    def _rate_limit_response(self) -> JSONResponse:
        """
        Create rate limit error response.
        
        Returns:
            429 Too Many Requests response
        """
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }
            },
            headers={
                "Retry-After": "60",
            }
        )
    
    def _add_rate_limit_headers(self, response: Response, client_ip: str) -> None:
        """
        Add rate limit information headers.
        
        Args:
            response: Response object
            client_ip: Client IP address
        """
        bucket = self._buckets.get(client_ip)
        if bucket:
            remaining = int(bucket["tokens"])
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    
    def _periodic_cleanup(self) -> None:
        """
        Periodically clean up old bucket entries.
        
        Removes buckets that haven't been used in the cleanup interval.
        """
        now = time.time()
        
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        # Remove old entries
        cutoff = now - self._cleanup_interval
        keys_to_remove = [
            ip for ip, bucket in self._buckets.items()
            if bucket["last_update"] < cutoff
        ]
        
        for ip in keys_to_remove:
            del self._buckets[ip]
        
        self._last_cleanup = now


def get_cors_middleware():
    """
    Get configured CORS middleware.
    
    Returns:
        CORSMiddleware instance configured from settings
    """
    return CORSMiddleware(
        app=None,  # Will be set by FastAPI
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )


def configure_cors(app) -> None:
    """
    Configure CORS middleware on FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
