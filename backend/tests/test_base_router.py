"""
Tests for base CRUD router.
"""
import pytest
from uuid import uuid4
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from app.schemas.base import CreateSchema, UpdateSchema, ResponseSchema
from app.api.base import BaseCRUDRouter


# Test model
class TestProduct(BaseModel):
    """Test product model."""
    __tablename__ = "test_products"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)


# Test schemas
class TestProductCreate(CreateSchema):
    """Test product create schema."""
    name: str
    price: float
    description: str | None = None


class TestProductUpdate(UpdateSchema):
    """Test product update schema."""
    name: str | None = None
    price: float | None = None
    description: str | None = None


class TestProductResponse(ResponseSchema):
    """Test product response schema."""
    name: str
    price: float
    description: str | None


@pytest.fixture
async def app(db_session):
    """Create test FastAPI app."""
    from app.core.database import Base
    
    # Create tables
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create app
    app = FastAPI()
    
    # Create router
    router = BaseCRUDRouter(
        model=TestProduct,
        create_schema=TestProductCreate,
        update_schema=TestProductUpdate,
        response_schema=TestProductResponse,
        prefix="/products",
        tags=["products"],
        include_hard_delete=True,
    ).router
    
    # Include router
    app.include_router(router)
    
    return app


@pytest.fixture
async def client(app):
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def product_data():
    """Product test data."""
    return {
        "name": "Test Product",
        "price": 99.99,
        "description": "A test product",
    }


class TestCreateEndpoint:
    """Test cases for POST / endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_success(self, client, product_data):
        """Test successful product creation."""
        response = await client.post("/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == product_data["name"]
        assert data["price"] == product_data["price"]
        assert data["description"] == product_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_minimal(self, client):
        """Test creation with minimal required fields."""
        response = await client.post(
            "/products/",
            json={"name": "Minimal Product", "price": 10.0},
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Product"
        assert data["price"] == 10.0
        assert data["description"] is None
    
    @pytest.mark.asyncio
    async def test_create_validation_error(self, client):
        """Test creation with invalid data."""
        response = await client.post(
            "/products/",
            json={"name": "No Price"},  # Missing required price field
        )
        
        assert response.status_code == 422  # Validation error


class TestGetByIdEndpoint:
    """Test cases for GET /{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, client, product_data):
        """Test successful retrieval by ID."""
        # Create product
        create_response = await client.post("/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Get product
        response = await client.get(f"/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == product_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, client):
        """Test retrieval of non-existent product."""
        fake_id = str(uuid4())
        response = await client.get(f"/products/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_by_id_invalid_uuid(self, client):
        """Test retrieval with invalid UUID."""
        response = await client.get("/products/invalid-uuid")
        
        assert response.status_code == 422  # Validation error


class TestListEndpoint:
    """Test cases for GET / endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_empty(self, client):
        """Test listing with no products."""
        response = await client.get("/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []
        assert data["page"] == 1
    
    @pytest.mark.asyncio
    async def test_list_with_data(self, client):
        """Test listing with multiple products."""
        # Create multiple products
        for i in range(5):
            await client.post(
                "/products/",
                json={"name": f"Product {i}", "price": 10.0 * i},
            )
        
        # List products
        response = await client.get("/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["data"]) == 5
        assert data["has_next"] is False
        assert data["has_previous"] is False
    
    @pytest.mark.asyncio
    async def test_list_pagination(self, client):
        """Test listing with pagination."""
        # Create 15 products
        for i in range(15):
            await client.post(
                "/products/",
                json={"name": f"Product {i}", "price": 10.0},
            )
        
        # Get first page
        response = await client.get("/products/?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["data"]) == 10
        assert data["page"] == 1
        assert data["total_pages"] == 2
        assert data["has_next"] is True
        assert data["has_previous"] is False
        
        # Get second page
        response = await client.get("/products/?page=2&page_size=10")
        
        data = response.json()
        assert len(data["data"]) == 5
        assert data["page"] == 2
        assert data["has_next"] is False
        assert data["has_previous"] is True
    
    @pytest.mark.asyncio
    async def test_list_sorting(self, client):
        """Test listing with sorting."""
        # Create products
        await client.post("/products/", json={"name": "Zebra", "price": 30.0})
        await client.post("/products/", json={"name": "Apple", "price": 10.0})
        await client.post("/products/", json={"name": "Mango", "price": 20.0})
        
        # Sort by name ascending
        response = await client.get("/products/?sort_by=name&sort_order=asc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"][0]["name"] == "Apple"
        assert data["data"][1]["name"] == "Mango"
        assert data["data"][2]["name"] == "Zebra"


class TestUpdateEndpoint:
    """Test cases for PUT /{id} and PATCH /{id} endpoints."""
    
    @pytest.mark.asyncio
    async def test_put_update_success(self, client, product_data):
        """Test full update with PUT."""
        # Create product
        create_response = await client.post("/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Update product
        update_data = {
            "name": "Updated Product",
            "price": 199.99,
            "description": "Updated description",
        }
        response = await client.put(f"/products/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["price"] == update_data["price"]
        assert data["description"] == update_data["description"]
    
    @pytest.mark.asyncio
    async def test_patch_partial_update(self, client, product_data):
        """Test partial update with PATCH."""
        # Create product
        create_response = await client.post("/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Partial update (only price)
        response = await client.patch(
            f"/products/{product_id}",
            json={"price": 149.99},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product_data["name"]  # Unchanged
        assert data["price"] == 149.99  # Updated
        assert data["description"] == product_data["description"]  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_not_found(self, client):
        """Test updating non-existent product."""
        fake_id = str(uuid4())
        response = await client.put(
            f"/products/{fake_id}",
            json={"name": "Test", "price": 10.0},
        )
        
        assert response.status_code == 404


class TestDeleteEndpoint:
    """Test cases for DELETE /{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_soft_delete_success(self, client, product_data):
        """Test soft delete."""
        # Create product
        create_response = await client.post("/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Delete product
        response = await client.delete(f"/products/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()
        assert data["detail"]["id"] == product_id
        
        # Verify product is not found (soft deleted)
        get_response = await client.get(f"/products/{product_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_not_found(self, client):
        """Test deleting non-existent product."""
        fake_id = str(uuid4())
        response = await client.delete(f"/products/{fake_id}")
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_hard_delete_success(self, client, product_data):
        """Test hard delete (permanent)."""
        # Create product
        create_response = await client.post("/products/", json=product_data)
        product_id = create_response.json()["id"]
        
        # Hard delete product
        response = await client.delete(f"/products/{product_id}/hard")
        
        assert response.status_code == 200
        data = response.json()
        assert "permanently deleted" in data["message"].lower()


class TestRouterFeatures:
    """Test cases for router features."""
    
    @pytest.mark.asyncio
    async def test_openapi_documentation(self, app):
        """Test that OpenAPI docs are generated."""
        # Get OpenAPI schema
        openapi_schema = app.openapi()
        
        # Verify paths exist
        assert "/products/" in openapi_schema["paths"]
        assert "/products/{id}" in openapi_schema["paths"]
        
        # Verify operations
        paths = openapi_schema["paths"]
        assert "post" in paths["/products/"]
        assert "get" in paths["/products/"]
        assert "get" in paths["/products/{id}"]
        assert "put" in paths["/products/{id}"]
        assert "patch" in paths["/products/{id}"]
        assert "delete" in paths["/products/{id}"]
    
    @pytest.mark.asyncio
    async def test_response_format(self, client, product_data):
        """Test that responses follow the expected format."""
        # Create product
        response = await client.post("/products/", json=product_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response includes system fields
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "is_deleted" in data
        
        # Verify response includes entity fields
        assert "name" in data
        assert "price" in data
        assert "description" in data
    
    @pytest.mark.asyncio
    async def test_list_response_format(self, client):
        """Test that list responses follow the paginated format."""
        # Create product
        await client.post(
            "/products/",
            json={"name": "Test", "price": 10.0},
        )
        
        # Get list
        response = await client.get("/products/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination metadata
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_previous" in data
