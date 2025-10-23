"""
Tests for position API endpoints.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.position import Position


@pytest.mark.asyncio
class TestPositionAPI:
    """Test suite for position API endpoints."""
    
    @pytest_asyncio.fixture
    async def sample_position(self, db_session: AsyncSession) -> Position:
        """Create a sample position for testing."""
        position = Position(
            name="Senior Software Engineer",
            code="SSE001",
            level=5,
            description="Senior level software engineer position",
            is_active=True,
        )
        db_session.add(position)
        await db_session.commit()
        await db_session.refresh(position)
        return position
    
    @pytest_asyncio.fixture
    async def inactive_position(self, db_session: AsyncSession) -> Position:
        """Create an inactive position for testing."""
        position = Position(
            name="Legacy Position",
            code="LEG001",
            level=3,
            description="Inactive legacy position",
            is_active=False,
        )
        db_session.add(position)
        await db_session.commit()
        await db_session.refresh(position)
        return position
    
    async def test_create_position(self, client: AsyncClient):
        """Test creating a new position."""
        data = {
            "name": "Junior Developer",
            "code": "JD001",
            "level": 2,
            "description": "Entry level developer position",
            "is_active": True,
        }
        
        response = await client.post("/api/v1/positions/", json=data)
        
        assert response.status_code == 201
        body = response.json()
        assert "data" in body
        result = body["data"]
        
        assert "id" in result
        assert result["name"] == data["name"]
        assert result["code"] == data["code"]
        assert result["level"] == data["level"]
        assert result["description"] == data["description"]
        assert result["is_active"] == data["is_active"]
        assert "created_at" in result
        assert "updated_at" in result
    
    async def test_create_position_duplicate_code(
        self, client: AsyncClient, sample_position: Position
    ):
        """Test creating position with duplicate code."""
        data = {
            "name": "Different Name",
            "code": sample_position.code,  # Duplicate code
            "level": 3,
            "description": "Another position",
            "is_active": True,
        }
        
        response = await client.post("/api/v1/positions/", json=data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()
    
    async def test_create_position_invalid_data(self, client: AsyncClient):
        """Test creating position with invalid data."""
        data = {
            "name": "",  # Empty name
            "code": "INV",
            "level": 0,  # Invalid level
            "is_active": True,
        }
        
        response = await client.post("/api/v1/positions/", json=data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_get_position_by_id(
        self, client: AsyncClient, sample_position: Position
    ):
        """Test getting a position by ID."""
        response = await client.get(f"/api/v1/positions/{sample_position.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(sample_position.id)
        assert result["name"] == sample_position.name
        assert result["code"] == sample_position.code
        assert result["level"] == sample_position.level
        assert result["description"] == sample_position.description
    
    async def test_get_position_not_found(self, client: AsyncClient):
        """Test getting a non-existent position."""
        fake_id = uuid4()
        response = await client.get(f"/api/v1/positions/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_list_positions(
        self, client: AsyncClient, sample_position: Position
    ):
        """Test listing positions with pagination."""
        response = await client.get(
            "/api/v1/positions/", 
            params={"page": 1, "page_size": 10}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "data" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert len(result["data"]) > 0
        
        # Check that sample position is in results
        position_ids = [p["id"] for p in result["data"]]
        assert str(sample_position.id) in position_ids
    
    async def test_list_positions_pagination(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test positions pagination."""
        # Create multiple positions
        for i in range(5):
            position = Position(
                name=f"Position {i}",
                code=f"POS{i:03d}",
                level=i + 1,
                description=f"Position description {i}",
                is_active=True,
            )
            db_session.add(position)
        await db_session.commit()
        
        # Test first page
        response = await client.get(
            "/api/v1/positions/", 
            params={"page": 1, "page_size": 2}
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["data"]) == 2
        assert result["total"] == 5
        assert result["page"] == 1
        assert result["page_size"] == 2
        
        # Test second page
        response = await client.get(
            "/api/v1/positions/", 
            params={"page": 2, "page_size": 2}
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["data"]) == 2
        assert result["page"] == 2
        
        # Verify different records on different pages
        first_ids = [p["id"] for p in result["data"]]
        response = await client.get(
            "/api/v1/positions/", 
            params={"page": 1, "page_size": 2}
        )
        second_ids = [p["id"] for p in response.json()["data"]]
        assert first_ids != second_ids
    
    async def test_list_positions_filter_active(
        self, client: AsyncClient, sample_position: Position, inactive_position: Position
    ):
        """Test filtering positions by is_active."""
        # Get only active positions
        response = await client.get(
            "/api/v1/positions/", 
            params={"is_active": True, "page": 1, "page_size": 10}
        )
        
        assert response.status_code == 200
        result = response.json()
        position_ids = [p["id"] for p in result["data"]]
        
        # Active position should be in results
        assert str(sample_position.id) in position_ids
        
        # Inactive position should NOT be in results
        assert str(inactive_position.id) not in position_ids
        
        # Verify all returned positions are active
        for position in result["data"]:
            assert position["is_active"] is True
    
    async def test_update_position(
        self, client: AsyncClient, sample_position: Position
    ):
        """Test updating a position."""
        data = {
            "name": "Updated Senior Engineer",
            "level": 6,
            "description": "Updated description",
        }
        
        response = await client.put(
            f"/api/v1/positions/{sample_position.id}", 
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["id"] == str(sample_position.id)
        assert result["name"] == data["name"]
        assert result["level"] == data["level"]
        assert result["description"] == data["description"]
        assert result["code"] == sample_position.code  # Code unchanged
    
    async def test_update_position_not_found(self, client: AsyncClient):
        """Test updating non-existent position."""
        fake_id = uuid4()
        data = {"name": "Updated Name"}
        
        response = await client.put(f"/api/v1/positions/{fake_id}", json=data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_update_position_duplicate_code(
        self, client: AsyncClient, sample_position: Position, db_session: AsyncSession
    ):
        """Test updating position with existing code."""
        # Create another position
        other_position = Position(
            name="Other Position",
            code="OTHER001",
            level=3,
            description="Another position",
            is_active=True,
        )
        db_session.add(other_position)
        await db_session.commit()
        await db_session.refresh(other_position)
        
        # Try to update sample_position with other's code
        data = {"code": other_position.code}
        
        response = await client.put(
            f"/api/v1/positions/{sample_position.id}", 
            json=data
        )
        
        assert response.status_code == 409
        assert "code" in response.json()["detail"].lower()
    
    async def test_delete_position(
        self, client: AsyncClient, sample_position: Position
    ):
        """Test soft deleting a position."""
        response = await client.delete(f"/api/v1/positions/{sample_position.id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result or "success" in str(result).lower()
        
        # Verify position is soft deleted (not in list)
        response = await client.get(f"/api/v1/positions/{sample_position.id}")
        assert response.status_code == 404
    
    async def test_delete_position_not_found(self, client: AsyncClient):
        """Test deleting non-existent position."""
        fake_id = uuid4()
        response = await client.delete(f"/api/v1/positions/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_list_positions_empty(self, client: AsyncClient):
        """Test listing positions when none exist."""
        response = await client.get(
            "/api/v1/positions/", 
            params={"page": 1, "page_size": 10}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["data"] == []
        assert result["total"] == 0
        assert result["page"] == 1
    
    async def test_position_with_department(self, client: AsyncClient):
        """Test creating position with department_id."""
        department_id = str(uuid4())
        data = {
            "name": "Department Position",
            "code": "DEPT001",
            "level": 4,
            "description": "Position with department",
            "department_id": department_id,
            "is_active": True,
        }
        
        response = await client.post("/api/v1/positions/", json=data)
        
        assert response.status_code == 201
        result = response.json()
        assert result["department_id"] == department_id
    
    async def test_list_positions_sorting(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test sorting positions."""
        # Create positions with different names
        positions = [
            Position(name="Alpha Position", code="ALPHA", level=1, is_active=True),
            Position(name="Beta Position", code="BETA", level=2, is_active=True),
            Position(name="Gamma Position", code="GAMMA", level=3, is_active=True),
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()
        
        # Test sorting by name ascending
        response = await client.get(
            "/api/v1/positions/",
            params={"page": 1, "page_size": 10, "sort_by": "name", "sort_order": "asc"}
        )
        
        assert response.status_code == 200
        result = response.json()
        names = [p["name"] for p in result["data"]]
        assert names == sorted(names)  # Verify ascending order
