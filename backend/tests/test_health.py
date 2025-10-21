"""
Test for health check endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["service"] == "CRM Backend API"
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_database_health_check(client: AsyncClient):
    """Test database health check endpoint."""
    response = await client.get("/api/v1/health/db")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert data["version"] == "0.1.0"
    assert "docs_url" in data