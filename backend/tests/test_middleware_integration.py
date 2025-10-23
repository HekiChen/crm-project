"""
Integration tests for complete middleware stack.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


# Test fixtures

import pytest
import time
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client():
    """
    Create test client with full middleware stack.
    
    Note: Uses function scope to ensure rate limit state is properly isolated
    between tests. In production, rate limits are per-IP, but in tests all
    requests come from the same test client.
    """
    # Wait to allow rate limit tokens to refill between tests
    # Token refill rate is 60 tokens/minute = 1 token/second
    # We wait 2 seconds to ensure clean state
    time.sleep(2)
    return TestClient(app)


# Test complete middleware flow

def test_middleware_stack_on_successful_request(client):
    """Test all middleware works together on successful request."""
    response = client.get("/api/v1/health")
    
    # Should succeed
    assert response.status_code == 200
    
    # Security headers should be present (from SecurityHeadersMiddleware)
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert "content-security-policy" in response.headers
    
    # Server header should be removed
    assert "server" not in response.headers
    
    # Rate limit headers should be present (from RateLimitMiddleware)
    assert "x-ratelimit-limit" in response.headers
    assert "x-ratelimit-remaining" in response.headers
    
    # Request ID should be present (from LoggingMiddleware)
    assert "x-request-id" in response.headers
    
    # Response should be formatted (from ResponseFormatterMiddleware)
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "request_id" in data["meta"]
    assert "timestamp" in data["meta"]


def test_middleware_stack_on_not_found(client):
    """Test middleware stack on 404 error."""
    response = client.get("/api/v1/nonexistent")
    
    # Should return 404
    assert response.status_code == 404
    
    # Security headers should still be present
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    
    # Error response should be formatted (from ErrorHandlerMiddleware)
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]
    assert "timestamp" in data["error"]


def test_cors_headers_present(client):
    """Test CORS middleware adds proper headers."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_preflight_request(client):
    """Test CORS preflight OPTIONS request."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    # Preflight should succeed
    assert response.status_code == 200
    
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers


def test_rate_limiting_enforcement(client):
    """Test rate limiting middleware blocks excessive requests."""
    # Make many requests to trigger rate limit
    # Default is 60 per minute, so make 65 requests
    responses = []
    for _ in range(65):
        response = client.get("/api/v1/health")
        responses.append(response)

    # Some requests should be rate limited
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0, "Expected some requests to be rate limited"

    # Rate limited response should have proper format
    if rate_limited:
        error_response = rate_limited[0]
        assert "retry-after" in error_response.headers

        data = error_response.json()
        assert "error" in data
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"

        # Rate limit headers should be present
        assert "x-ratelimit-limit" in error_response.headers
        assert "x-ratelimit-remaining" in error_response.headers
def test_request_id_propagation(client):
    """Test request ID is propagated through all middleware."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    
    # Request ID should be in headers
    request_id_header = response.headers.get("x-request-id")
    assert request_id_header is not None
    
    # Request ID should be in response body
    data = response.json()
    assert "meta" in data
    assert "request_id" in data["meta"]
    
    # Should be the same ID
    assert data["meta"]["request_id"] == request_id_header


def test_middleware_order_security_wraps_errors(client):
    """Test security headers are applied even to error responses."""
    # Trigger a 404 error
    response = client.get("/api/v1/does-not-exist")
    
    assert response.status_code == 404
    
    # Security headers should be present on error
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert "content-security-policy" in response.headers


def test_root_endpoint_with_middleware(client):
    """Test root endpoint works with all middleware."""
    response = client.get("/")
    
    assert response.status_code == 200
    
    # Security headers should be present
    assert "x-frame-options" in response.headers
    
    # Rate limit headers should be present
    assert "x-ratelimit-limit" in response.headers
    
    # Response should be formatted
    data = response.json()
    assert "data" in data
    assert "meta" in data


def test_middleware_performance(client):
    """Test middleware stack doesn't significantly impact performance."""
    import time
    
    start = time.time()
    response = client.get("/api/v1/health")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    
    # Should respond quickly (within 100ms for simple endpoint)
    assert elapsed < 0.1, f"Request took {elapsed}s, expected < 0.1s"


def test_multiple_requests_maintain_isolation(client):
    """Test multiple requests are properly isolated."""
    # Make several requests
    responses = [client.get("/api/v1/health") for _ in range(5)]
    
    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    
    # Each should have unique request ID
    request_ids = [r.headers.get("x-request-id") for r in responses]
    assert len(set(request_ids)) == 5, "Request IDs should be unique"


def test_error_handling_with_full_stack(client):
    """Test error handling works correctly with full middleware stack."""
    # This will trigger 404 since endpoint doesn't exist
    response = client.post("/api/v1/nonexistent", json={"test": "data"})
    
    assert response.status_code == 404
    
    # Should have all expected headers and formatting
    assert "x-request-id" in response.headers
    assert "x-frame-options" in response.headers
    
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]
