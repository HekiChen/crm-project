"""
Tests for base Pydantic schemas.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.base import (
    BaseSchema,
    CreateSchema,
    UpdateSchema,
    ResponseSchema,
    IDResponse,
    ListResponseSchema,
    PaginationParams,
    MessageResponse,
    ErrorDetail,
    ErrorResponse,
)


# Test schemas for testing
class TestUserCreate(CreateSchema):
    """Test create schema."""
    username: str
    email: str


class TestUserUpdate(UpdateSchema):
    """Test update schema."""
    username: str | None = None
    email: str | None = None


class TestUserResponse(ResponseSchema):
    """Test response schema."""
    username: str
    email: str


class TestBaseSchema:
    """Test cases for BaseSchema."""
    
    def test_base_schema_config(self):
        """Test that BaseSchema has correct configuration."""
        config = BaseSchema.model_config
        
        assert config["from_attributes"] is True
        assert config["populate_by_name"] is True
        assert config["use_enum_values"] is True
    
    def test_create_schema_inheritance(self):
        """Test that CreateSchema can be inherited."""
        user_create = TestUserCreate(username="john", email="john@example.com")
        
        assert user_create.username == "john"
        assert user_create.email == "john@example.com"
    
    def test_update_schema_optional_fields(self):
        """Test that UpdateSchema supports partial updates."""
        # Only update username
        user_update = TestUserUpdate(username="jane")
        
        assert user_update.username == "jane"
        assert user_update.email is None
        
        # Only update email
        user_update2 = TestUserUpdate(email="jane@example.com")
        
        assert user_update2.username is None
        assert user_update2.email == "jane@example.com"


class TestResponseSchema:
    """Test cases for ResponseSchema."""
    
    def test_response_schema_fields(self):
        """Test that ResponseSchema includes all required fields."""
        user_id = uuid4()
        now = datetime.utcnow()
        
        response = TestUserResponse(
            id=user_id,
            username="test",
            email="test@example.com",
            created_at=now,
            updated_at=now,
            is_deleted=False,
            deleted_at=None,
            created_by_id=None,
            updated_by_id=None,
        )
        
        assert response.id == user_id
        assert response.username == "test"
        assert response.email == "test@example.com"
        assert response.created_at == now
        assert response.updated_at == now
        assert response.is_deleted is False
    
    def test_response_schema_from_orm(self):
        """Test that ResponseSchema can be created from ORM model."""
        # Simulate ORM model with attributes
        class MockUser:
            id = uuid4()
            username = "mock"
            email = "mock@example.com"
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
            is_deleted = False
            deleted_at = None
            created_by_id = None
            updated_by_id = None
        
        mock_user = MockUser()
        response = TestUserResponse.model_validate(mock_user)
        
        assert response.id == mock_user.id
        assert response.username == mock_user.username


class TestIDResponse:
    """Test cases for IDResponse."""
    
    def test_id_response(self):
        """Test IDResponse schema."""
        user_id = uuid4()
        response = IDResponse(id=user_id)
        
        assert response.id == user_id


class TestListResponseSchema:
    """Test cases for ListResponseSchema."""
    
    def test_create_list_response_first_page(self):
        """Test creating a list response for first page."""
        users = [
            TestUserResponse(
                id=uuid4(),
                username=f"user{i}",
                email=f"user{i}@example.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_deleted=False,
            )
            for i in range(10)
        ]
        
        response = ListResponseSchema[TestUserResponse].create(
            data=users,
            total=50,
            page=1,
            page_size=10,
        )
        
        assert len(response.data) == 10
        assert response.total == 50
        assert response.page == 1
        assert response.page_size == 10
        assert response.total_pages == 5
        assert response.has_next is True
        assert response.has_previous is False
    
    def test_create_list_response_middle_page(self):
        """Test creating a list response for middle page."""
        response = ListResponseSchema[TestUserResponse].create(
            data=[],
            total=100,
            page=5,
            page_size=10,
        )
        
        assert response.total_pages == 10
        assert response.has_next is True
        assert response.has_previous is True
    
    def test_create_list_response_last_page(self):
        """Test creating a list response for last page."""
        response = ListResponseSchema[TestUserResponse].create(
            data=[],
            total=100,
            page=10,
            page_size=10,
        )
        
        assert response.has_next is False
        assert response.has_previous is True
    
    def test_create_list_response_empty(self):
        """Test creating a list response with no data."""
        response = ListResponseSchema[TestUserResponse].create(
            data=[],
            total=0,
            page=1,
            page_size=10,
        )
        
        assert response.total == 0
        assert response.total_pages == 0
        assert response.has_next is False
        assert response.has_previous is False


class TestPaginationParams:
    """Test cases for PaginationParams."""
    
    def test_default_pagination(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.page_size == 20
        assert params.sort_by is None
        assert params.sort_order == "desc"
    
    def test_custom_pagination(self):
        """Test custom pagination parameters."""
        params = PaginationParams(
            page=3,
            page_size=50,
            sort_by="created_at",
            sort_order="asc",
        )
        
        assert params.page == 3
        assert params.page_size == 50
        assert params.sort_by == "created_at"
        assert params.sort_order == "asc"
    
    def test_skip_calculation(self):
        """Test skip property calculation."""
        params = PaginationParams(page=1, page_size=10)
        assert params.skip == 0
        
        params = PaginationParams(page=2, page_size=10)
        assert params.skip == 10
        
        params = PaginationParams(page=5, page_size=25)
        assert params.skip == 100
    
    def test_limit_property(self):
        """Test limit property."""
        params = PaginationParams(page_size=30)
        assert params.limit == 30
    
    def test_pagination_validation(self):
        """Test that invalid pagination params are rejected."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            PaginationParams(page=0)  # page must be >= 1
        
        with pytest.raises(Exception):
            PaginationParams(page_size=0)  # page_size must be >= 1
        
        with pytest.raises(Exception):
            PaginationParams(page_size=101)  # page_size must be <= 100


class TestMessageResponse:
    """Test cases for MessageResponse."""
    
    def test_simple_message(self):
        """Test simple message response."""
        response = MessageResponse(message="Operation successful")
        
        assert response.message == "Operation successful"
        assert response.detail is None
    
    def test_message_with_detail(self):
        """Test message response with additional details."""
        response = MessageResponse(
            message="User created",
            detail={"user_id": str(uuid4()), "username": "john"}
        )
        
        assert response.message == "User created"
        assert response.detail is not None
        assert "user_id" in response.detail


class TestErrorResponse:
    """Test cases for ErrorResponse."""
    
    def test_simple_error(self):
        """Test simple error response."""
        error = ErrorResponse(
            code="NOT_FOUND",
            message="User not found",
        )
        
        assert error.code == "NOT_FOUND"
        assert error.message == "User not found"
        assert error.details is None
        assert isinstance(error.timestamp, datetime)
    
    def test_error_with_details(self):
        """Test error response with field details."""
        error = ErrorResponse(
            code="VALIDATION_ERROR",
            message="Invalid input",
            details=[
                ErrorDetail(
                    field="email",
                    message="Invalid email format",
                    type="value_error.email"
                ),
                ErrorDetail(
                    field="age",
                    message="Must be at least 18",
                    type="value_error.number.not_ge"
                ),
            ],
            request_id="req_123",
        )
        
        assert error.code == "VALIDATION_ERROR"
        assert error.details is not None
        assert len(error.details) == 2
        assert error.details[0].field == "email"
        assert error.request_id == "req_123"
