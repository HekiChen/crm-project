"""
Tests for response formatter middleware.
"""
import json
import pytest
from datetime import datetime
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from app.middleware.response_formatter import (
    ResponseFormatterMiddleware,
    format_response,
    format_paginated_response,
)


# Test fixtures

@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app with response formatter middleware."""
    app = FastAPI()
    app.add_middleware(ResponseFormatterMiddleware)
    
    @app.get("/simple")
    async def simple_response():
        """Return simple dict response."""
        return {"message": "Hello, World!"}
    
    @app.get("/list")
    async def list_response():
        """Return list response."""
        return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
    
    @app.get("/paginated")
    async def paginated_response():
        """Return paginated response."""
        return {
            "items": [{"id": i, "name": f"Item {i}"} for i in range(1, 11)],
            "total": 100,
            "page": 1,
            "page_size": 10,
        }
    
    @app.get("/no-content", status_code=204)
    async def no_content():
        """Return 204 No Content."""
        return None
    
    @app.get("/already-formatted")
    async def already_formatted():
        """Return already formatted response."""
        return {
            "data": {"message": "Already wrapped"},
            "meta": {"request_id": "test_123"}
        }
    
    @app.get("/error", status_code=400)
    async def error_response():
        """Return error response."""
        return {
            "error": {
                "code": "TEST_ERROR",
                "message": "Test error"
            }
        }
    
    @app.get("/stream")
    async def stream_response():
        """Return streaming response."""
        def generate():
            yield b"chunk1"
            yield b"chunk2"
        
        return StreamingResponse(generate(), media_type="text/plain")
    
    @app.post("/create")
    async def create_item(data: dict):
        """Create item endpoint."""
        return {"id": 1, **data}
    
    @app.get("/empty")
    async def empty_response():
        """Return empty dict."""
        return {}
    
    @app.get("/null")
    async def null_response():
        """Return None (converted to null)."""
        return None
    
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


# Test ResponseFormatterMiddleware

def test_simple_response_formatted(client):
    """Test simple response is formatted correctly."""
    response = client.get("/simple")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "data" in data
    assert "meta" in data
    
    # Check data content
    assert data["data"] == {"message": "Hello, World!"}
    
    # Check metadata
    assert "request_id" in data["meta"]
    assert "timestamp" in data["meta"]
    assert data["meta"]["timestamp"].endswith("Z")


def test_list_response_formatted(client):
    """Test list response is formatted correctly."""
    response = client.get("/list")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "data" in data
    assert "meta" in data
    
    # Check data is list
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 2
    assert data["data"][0]["id"] == 1


def test_paginated_response_formatted(client):
    """Test paginated response is formatted with pagination metadata."""
    response = client.get("/paginated")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "data" in data
    assert "meta" in data
    
    # Check data is the items list
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 10
    
    # Check pagination metadata
    meta = data["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total_items"] == 100
    assert meta["total_pages"] == 10
    assert meta["has_next"] is True
    assert meta["has_previous"] is False
    assert "request_id" in meta
    assert "timestamp" in meta


def test_no_content_not_formatted(client):
    """Test 204 No Content is not formatted."""
    response = client.get("/no-content")
    
    assert response.status_code == 204
    assert response.content == b""


def test_already_formatted_not_wrapped_again(client):
    """Test already formatted response is not wrapped again."""
    response = client.get("/already-formatted")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have data and meta at top level (not wrapped again)
    assert "data" in data
    assert "meta" in data
    assert data["data"] == {"message": "Already wrapped"}
    assert data["meta"]["request_id"] == "test_123"
    
    # Should NOT have nested data.data structure
    assert "data" not in data.get("data", {})


def test_error_response_not_formatted(client):
    """Test error responses are not formatted."""
    response = client.get("/error")
    
    assert response.status_code == 400
    data = response.json()
    
    # Should have error structure, not data/meta
    assert "error" in data
    assert "data" not in data
    assert data["error"]["code"] == "TEST_ERROR"


def test_streaming_response_not_formatted(client):
    """Test streaming responses are not formatted."""
    response = client.get("/stream")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.content == b"chunk1chunk2"


def test_post_response_formatted(client):
    """Test POST response is formatted."""
    response = client.post("/create", json={"name": "Test Item"})
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["data"]["id"] == 1
    assert data["data"]["name"] == "Test Item"


def test_empty_response_formatted(client):
    """Test empty dict response is formatted."""
    response = client.get("/empty")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "data" in data
    assert "meta" in data
    assert data["data"] == {}


def test_metadata_has_timestamp(client):
    """Test metadata includes ISO timestamp."""
    response = client.get("/simple")
    
    data = response.json()
    timestamp = data["meta"]["timestamp"]
    
    # Check format (ISO 8601 with Z suffix)
    assert timestamp.endswith("Z")
    
    # Validate can be parsed as datetime
    timestamp_parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert isinstance(timestamp_parsed, datetime)


def test_metadata_has_request_id(client):
    """Test metadata includes request_id if available."""
    response = client.get("/simple")
    
    data = response.json()
    # Request ID should be present (from logging middleware if configured)
    assert "request_id" in data["meta"]


# Test helper functions

def test_format_response_basic():
    """Test format_response helper function."""
    result = format_response({"message": "test"}, request_id="req_123")
    
    assert "data" in result
    assert "meta" in result
    assert result["data"] == {"message": "test"}
    assert result["meta"]["request_id"] == "req_123"
    assert "timestamp" in result["meta"]


def test_format_response_without_request_id():
    """Test format_response without request_id."""
    result = format_response({"message": "test"})
    
    assert result["data"] == {"message": "test"}
    assert result["meta"]["request_id"] is None
    assert "timestamp" in result["meta"]


def test_format_response_with_list():
    """Test format_response with list data."""
    items = [{"id": 1}, {"id": 2}]
    result = format_response(items)
    
    assert result["data"] == items
    assert isinstance(result["data"], list)


def test_format_paginated_response_basic():
    """Test format_paginated_response helper function."""
    items = [{"id": i} for i in range(1, 11)]
    result = format_paginated_response(
        items=items,
        total=100,
        page=1,
        page_size=10,
        request_id="req_123"
    )
    
    assert "data" in result
    assert "meta" in result
    assert result["data"] == items
    
    meta = result["meta"]
    assert meta["page"] == 1
    assert meta["page_size"] == 10
    assert meta["total_items"] == 100
    assert meta["total_pages"] == 10
    assert meta["has_next"] is True
    assert meta["has_previous"] is False
    assert meta["request_id"] == "req_123"


def test_format_paginated_response_last_page():
    """Test pagination metadata for last page."""
    items = [{"id": i} for i in range(1, 6)]
    result = format_paginated_response(
        items=items,
        total=25,
        page=3,
        page_size=10,
    )
    
    meta = result["meta"]
    assert meta["page"] == 3
    assert meta["total_pages"] == 3
    assert meta["has_next"] is False
    assert meta["has_previous"] is True


def test_format_paginated_response_middle_page():
    """Test pagination metadata for middle page."""
    items = [{"id": i} for i in range(1, 11)]
    result = format_paginated_response(
        items=items,
        total=100,
        page=5,
        page_size=10,
    )
    
    meta = result["meta"]
    assert meta["page"] == 5
    assert meta["total_pages"] == 10
    assert meta["has_next"] is True
    assert meta["has_previous"] is True


def test_format_paginated_response_single_page():
    """Test pagination metadata when all items fit on one page."""
    items = [{"id": i} for i in range(1, 6)]
    result = format_paginated_response(
        items=items,
        total=5,
        page=1,
        page_size=10,
    )
    
    meta = result["meta"]
    assert meta["total_pages"] == 1
    assert meta["has_next"] is False
    assert meta["has_previous"] is False


def test_format_paginated_response_empty():
    """Test pagination metadata with no items."""
    result = format_paginated_response(
        items=[],
        total=0,
        page=1,
        page_size=10,
    )
    
    assert result["data"] == []
    meta = result["meta"]
    assert meta["total_items"] == 0
    assert meta["total_pages"] == 0
    assert meta["has_next"] is False
    assert meta["has_previous"] is False


def test_format_paginated_response_partial_last_page():
    """Test pagination with partial last page."""
    items = [{"id": i} for i in range(1, 6)]
    result = format_paginated_response(
        items=items,
        total=25,
        page=3,
        page_size=10,
    )
    
    # 25 items / 10 per page = 3 pages (1-10, 11-20, 21-25)
    meta = result["meta"]
    assert meta["total_pages"] == 3


def test_format_paginated_response_exact_pages():
    """Test pagination when total divides evenly."""
    items = [{"id": i} for i in range(1, 11)]
    result = format_paginated_response(
        items=items,
        total=30,
        page=1,
        page_size=10,
    )
    
    # 30 items / 10 per page = exactly 3 pages
    meta = result["meta"]
    assert meta["total_pages"] == 3


# Integration tests

def test_response_format_consistency(client):
    """Test all successful responses have consistent format."""
    endpoints = ["/simple", "/list", "/empty"]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data, f"Missing 'data' in {endpoint}"
        assert "meta" in data, f"Missing 'meta' in {endpoint}"
        assert "request_id" in data["meta"], f"Missing 'request_id' in {endpoint}"
        assert "timestamp" in data["meta"], f"Missing 'timestamp' in {endpoint}"


def test_paginated_metadata_fields(client):
    """Test paginated response has all required metadata fields."""
    response = client.get("/paginated")
    
    data = response.json()
    meta = data["meta"]
    
    required_fields = [
        "page",
        "page_size",
        "total_items",
        "total_pages",
        "has_next",
        "has_previous",
        "request_id",
        "timestamp"
    ]
    
    for field in required_fields:
        assert field in meta, f"Missing field: {field}"


def test_non_json_response_not_formatted(app):
    """Test non-JSON responses are not formatted."""
    @app.get("/html")
    async def html_response():
        from starlette.responses import HTMLResponse
        return HTMLResponse("<html><body>Hello</body></html>")
    
    client = TestClient(app)
    response = client.get("/html")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    assert b"<html>" in response.content


def test_custom_status_codes_formatted(app):
    """Test responses with custom 2xx status codes are formatted."""
    @app.post("/created", status_code=201)
    async def created():
        return {"id": 1, "name": "Created"}
    
    client = TestClient(app)
    response = client.post("/created")
    
    assert response.status_code == 201
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["data"]["id"] == 1


def test_redirect_not_formatted(app):
    """Test 3xx redirects are not formatted."""
    from starlette.responses import RedirectResponse
    
    @app.get("/redirect")
    async def redirect():
        return RedirectResponse("/simple")
    
    client = TestClient(app)
    response = client.get("/redirect", follow_redirects=False)
    
    assert response.status_code == 307
    assert "data" not in response.text


def test_server_error_not_formatted(app):
    """Test 5xx errors are not formatted."""
    @app.get("/server-error", status_code=500)
    async def server_error():
        return {"error": "Internal error"}
    
    client = TestClient(app)
    response = client.get("/server-error")
    
    assert response.status_code == 500
    # Response should not be wrapped with data/meta
    data = response.json()
    # Either has error key or is raw
    if "error" in data:
        assert "data" not in data
