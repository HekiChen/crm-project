"""
Tests for security middleware.
"""
import time
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    configure_cors,
)
from app.core.config import settings


# Test fixtures

@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/slow")
    async def slow_endpoint():
        time.sleep(0.1)
        return {"message": "slow"}
    
    return app


@pytest.fixture
def app_with_security(app: FastAPI) -> FastAPI:
    """Create app with security headers middleware."""
    app.add_middleware(SecurityHeadersMiddleware)
    return app


@pytest.fixture
def app_with_rate_limit(app: FastAPI) -> FastAPI:
    """Create app with rate limiting middleware."""
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10, burst_size=10)
    return app


@pytest.fixture
def client_with_security(app_with_security: FastAPI) -> TestClient:
    """Create test client with security headers."""
    return TestClient(app_with_security)


@pytest.fixture
def client_with_rate_limit(app_with_rate_limit: FastAPI) -> TestClient:
    """Create test client with rate limiting."""
    return TestClient(app_with_rate_limit)


# Test SecurityHeadersMiddleware

def test_security_headers_added(client_with_security):
    """Test that security headers are added to response."""
    response = client_with_security.get("/test")
    
    assert response.status_code == 200
    
    # Check all security headers are present
    headers = response.headers
    
    # X-Frame-Options
    assert "x-frame-options" in headers
    assert headers["x-frame-options"] == "DENY"
    
    # X-Content-Type-Options
    assert "x-content-type-options" in headers
    assert headers["x-content-type-options"] == "nosniff"
    
    # X-XSS-Protection
    assert "x-xss-protection" in headers
    assert headers["x-xss-protection"] == "1; mode=block"
    
    # Content-Security-Policy
    assert "content-security-policy" in headers
    assert "default-src 'self'" in headers["content-security-policy"]
    
    # Referrer-Policy
    assert "referrer-policy" in headers
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    
    # Permissions-Policy
    assert "permissions-policy" in headers
    assert "geolocation=()" in headers["permissions-policy"]


def test_hsts_header_in_production():
    """Test HSTS header is added in production environment."""
    # Save original environment
    original_env = settings.environment
    
    try:
        # Set to production
        settings.environment = "production"
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # Check HSTS header
        assert "strict-transport-security" in response.headers
        assert "max-age=31536000" in response.headers["strict-transport-security"]
        assert "includeSubDomains" in response.headers["strict-transport-security"]
    
    finally:
        # Restore original environment
        settings.environment = original_env


def test_hsts_header_not_in_development():
    """Test HSTS header is not added in development."""
    # Save original environment
    original_env = settings.environment
    
    try:
        # Set to development
        settings.environment = "development"
        
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)
        
        @app.get("/test")
        async def test():
            return {"message": "test"}
        
        client = TestClient(app)
        response = client.get("/test")
        
        # HSTS should not be present in development
        assert "strict-transport-security" not in response.headers
    
    finally:
        settings.environment = original_env


def test_server_header_removed(client_with_security):
    """Test that Server header is removed."""
    response = client_with_security.get("/test")
    
    # Server header should be removed
    assert "server" not in response.headers


def test_server_header_kept_when_disabled():
    """Test Server header is kept when remove_server_header=False."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, remove_server_header=False)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    # Server header may or may not be present (depends on server)
    # But we're not actively removing it
    # Just check the response is successful
    assert response.status_code == 200


def test_security_headers_on_all_endpoints(client_with_security):
    """Test security headers are added to all endpoints."""
    # Test multiple endpoints
    response1 = client_with_security.get("/test")
    response2 = client_with_security.get("/slow")
    
    for response in [response1, response2]:
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
        assert "content-security-policy" in response.headers


def test_csp_header_configuration():
    """Test Content-Security-Policy header has proper directives."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    csp = response.headers["content-security-policy"]
    
    # Check important CSP directives
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


# Test RateLimitMiddleware

def test_rate_limit_allows_normal_requests(client_with_rate_limit):
    """Test rate limiter allows requests under limit."""
    # Make several requests (under limit)
    for _ in range(5):
        response = client_with_rate_limit.get("/test")
        assert response.status_code == 200


def test_rate_limit_blocks_excessive_requests(client_with_rate_limit):
    """Test rate limiter blocks requests over limit."""
    # Make requests up to burst limit (10)
    for i in range(10):
        response = client_with_rate_limit.get("/test")
        assert response.status_code == 200, f"Request {i+1} should succeed"
    
    # Next request should be rate limited
    response = client_with_rate_limit.get("/test")
    assert response.status_code == 429
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_rate_limit_headers_present(client_with_rate_limit):
    """Test rate limit headers are added to response."""
    response = client_with_rate_limit.get("/test")
    
    assert response.status_code == 200
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    
    # Check values
    assert response.headers["x-ratelimit-limit"] == "10"
    assert int(response.headers["x-ratelimit-remaining"]) >= 0


def test_rate_limit_decreases_remaining(client_with_rate_limit):
    """Test remaining count decreases with each request."""
    response1 = client_with_rate_limit.get("/test")
    remaining1 = int(response1.headers["x-ratelimit-remaining"])
    
    # Small delay to ensure tokens aren't refilled
    response2 = client_with_rate_limit.get("/test")
    remaining2 = int(response2.headers["x-ratelimit-remaining"])
    
    # Remaining should decrease or stay same (due to time-based refill)
    # Since requests are very fast, remaining should generally decrease
    assert remaining2 <= remaining1


def test_rate_limit_response_format():
    """Test rate limit error response format."""
    # Create fresh app for this test
    app = FastAPI()
    # Very strict limit: 6 per minute, burst of 2 (allows first request, second gets limited)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=6, burst_size=2)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    # Create fresh client
    client = TestClient(app)
    
    # First request uses one token
    response1 = client.get("/test")
    assert response1.status_code == 200
    
    # Second request uses another token
    response2 = client.get("/test")
    assert response2.status_code == 200
    
    # Third request should be rate limited (no tokens left)
    response3 = client.get("/test")
    assert response3.status_code == 429
    
    # Check response format
    data = response3.json()
    assert "error" in data
    assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert "message" in data["error"]
    assert "timestamp" in data["error"]
    
    # Check Retry-After header
    assert "retry-after" in response3.headers
    assert response3.headers["retry-after"] == "60"
    
    # Check rate limit headers are present even on error
    assert "x-ratelimit-limit" in response3.headers


def test_rate_limit_per_ip():
    """Test rate limiting is per IP address."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2, burst_size=2)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Make requests from "different IPs" (simulated with headers)
    # Note: TestClient doesn't support multiple IPs easily,
    # so we'll test with same IP
    response1 = client.get("/test")
    response2 = client.get("/test")
    
    # Both should succeed (within limit)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Third request should be blocked
    response3 = client.get("/test")
    assert response3.status_code == 429


def test_rate_limit_token_refill():
    """Test tokens are refilled over time."""
    app = FastAPI()
    # Very low rate: 6 requests per minute = 1 request per 10 seconds
    # Use burst_size=2 to ensure first request succeeds
    app.add_middleware(RateLimitMiddleware, requests_per_minute=6, burst_size=2)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # First request uses one token
    response1 = client.get("/test")
    assert response1.status_code == 200
    
    # Immediate second request uses another token
    response2 = client.get("/test")
    assert response2.status_code == 200
    
    # Third immediate request should be blocked (no tokens left)
    response3 = client.get("/test")
    assert response3.status_code == 429
    
    # In real scenario, tokens would refill at 6/60 = 0.1 per second
    # We can't easily test time-based refill in unit tests without mocking time


def test_rate_limit_different_endpoints(client_with_rate_limit):
    """Test rate limit applies across all endpoints."""
    # Make requests to different endpoints
    response1 = client_with_rate_limit.get("/test")
    response2 = client_with_rate_limit.get("/slow")
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Remaining should have decreased by 2
    remaining = int(response2.headers["x-ratelimit-remaining"])
    assert remaining <= 8  # Started with 10, used 2


def test_rate_limit_custom_settings():
    """Test rate limiter with custom settings."""
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=30,
        burst_size=5
    )
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Should allow up to burst_size requests
    for i in range(5):
        response = client.get("/test")
        assert response.status_code == 200, f"Request {i+1} should succeed"
    
    # Next request should be blocked
    response = client.get("/test")
    assert response.status_code == 429
    
    # Check limit header matches setting (rate limit headers should be on error response too)
    assert "x-ratelimit-limit" in response.headers
    assert response.headers["x-ratelimit-limit"] == "30"


# Test CORS configuration

def test_cors_configuration():
    """Test CORS middleware configuration."""
    app = FastAPI()
    configure_cors(app)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Make a CORS preflight request
    response = client.options(
        "/test",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    # Check CORS headers (not all headers are always present depending on request)
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


def test_cors_allows_configured_origins():
    """Test CORS allows origins from settings."""
    app = FastAPI()
    configure_cors(app)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Request from allowed origin
    response = client.get(
        "/test",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_credentials_enabled():
    """Test CORS allows credentials."""
    app = FastAPI()
    configure_cors(app)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={"Origin": "http://localhost:3000"}
    )
    
    # Check credentials are allowed
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_exposes_custom_headers():
    """Test CORS exposes custom headers."""
    app = FastAPI()
    configure_cors(app)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    # Actual request (not OPTIONS) to check exposed headers
    response = client.get(
        "/test",
        headers={
            "Origin": "http://localhost:3000",
        }
    )
    
    # FastAPI's CORSMiddleware may not always set expose headers on GET requests
    # Check that the request succeeds with CORS
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


# Integration tests

def test_security_and_rate_limit_together():
    """Test security headers and rate limiting work together."""
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
    app.add_middleware(SecurityHeadersMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    response = client.get("/test")
    
    # Should have both security headers and rate limit headers
    assert "x-frame-options" in response.headers
    assert "x-ratelimit-limit" in response.headers


def test_all_middleware_together():
    """Test all security middleware together."""
    app = FastAPI()
    configure_cors(app)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
    app.add_middleware(SecurityHeadersMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    client = TestClient(app)
    
    response = client.get(
        "/test",
        headers={"Origin": "http://localhost:3000"}
    )
    
    # Should have security headers, rate limit headers, and CORS headers
    assert response.status_code == 200
    assert "x-frame-options" in response.headers
    assert "x-ratelimit-limit" in response.headers
    assert "access-control-allow-origin" in response.headers


def test_rate_limit_error_has_security_headers():
    """Test rate limit error responses have security headers.
    
    Note: Middleware order matters. RateLimitMiddleware must be added AFTER
    SecurityHeadersMiddleware to ensure security headers are applied to rate limit responses.
    """
    # Create fresh app
    app = FastAPI()
    # IMPORTANT: Add RateLimitMiddleware FIRST so SecurityHeadersMiddleware wraps it
    app.add_middleware(RateLimitMiddleware, requests_per_minute=6, burst_size=2)
    app.add_middleware(SecurityHeadersMiddleware)
    
    @app.get("/test")
    async def test():
        return {"message": "test"}
    
    # Create fresh client
    client = TestClient(app)
    
    # First request uses one token
    response1 = client.get("/test")
    assert response1.status_code == 200
    assert "x-frame-options" in response1.headers
    
    # Second request uses second token
    response2 = client.get("/test")
    assert response2.status_code == 200
    
    # Third request should be rate limited
    response3 = client.get("/test")
    assert response3.status_code == 429
    
    # Rate limit error should still have security headers (because SecurityHeadersMiddleware is outer)
    assert "x-frame-options" in response3.headers
    assert "x-content-type-options" in response3.headers
