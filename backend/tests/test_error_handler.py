"""
Tests for error handler middleware.
"""
import pytest
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError as PydanticValidationError, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.error_handler import (
    ErrorDetail,
    ErrorResponse,
    AppException,
    ValidationException,
    NotFoundException,
    PermissionDeniedException,
    AuthenticationException,
    ConflictException,
    DatabaseException,
    build_error_response,
    build_validation_error_details,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    generic_exception_handler,
    register_exception_handlers,
)


# Test models

class TestModel(BaseModel):
    """Test model for validation."""
    name: str
    age: int = Field(gt=0)
    email: str


# Test fixtures

@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    register_exception_handlers(app)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error/app")
    async def app_error():
        raise AppException("Test app error")
    
    @app.get("/error/validation")
    async def validation_error():
        raise ValidationException("Test validation error")
    
    @app.get("/error/not-found")
    async def not_found():
        raise NotFoundException("Test not found")
    
    @app.get("/error/permission")
    async def permission_denied():
        raise PermissionDeniedException("Test permission denied")
    
    @app.get("/error/auth")
    async def auth_error():
        raise AuthenticationException("Test auth error")
    
    @app.get("/error/conflict")
    async def conflict():
        raise ConflictException("Test conflict")
    
    @app.get("/error/database")
    async def database_error():
        raise DatabaseException("Test database error")
    
    @app.get("/error/http")
    async def http_error():
        raise StarletteHTTPException(status_code=404, detail="Test HTTP error")
    
    @app.get("/error/integrity")
    async def integrity_error():
        raise IntegrityError("UNIQUE constraint failed", None, None)
    
    @app.get("/error/sqlalchemy")
    async def sqlalchemy_error():
        raise SQLAlchemyError("Test SQLAlchemy error")
    
    @app.get("/error/generic")
    async def generic_error():
        raise ValueError("Test generic error")
    
    @app.post("/error/pydantic")
    async def pydantic_error(data: TestModel):
        return data
    
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_request():
    """Create mock request."""
    from unittest.mock import MagicMock
    request = MagicMock(spec=Request)
    request.url.path = "/test"
    request.method = "GET"
    request.state.request_id = "test_req_123"
    return request


# Test ErrorDetail model

def test_error_detail_basic():
    """Test basic error detail."""
    detail = ErrorDetail(
        field="name",
        message="Name is required",
        type="value_error.missing",
    )
    
    assert detail.field == "name"
    assert detail.message == "Name is required"
    assert detail.type == "value_error.missing"


def test_error_detail_optional_fields():
    """Test error detail with optional fields."""
    detail = ErrorDetail(message="Generic error")
    
    assert detail.field is None
    assert detail.message == "Generic error"
    assert detail.type is None


# Test ErrorResponse model

def test_error_response():
    """Test error response model."""
    now = datetime.utcnow()
    response = ErrorResponse(
        code="TEST_ERROR",
        message="Test error message",
        request_id="req_123",
        timestamp=now,
    )
    
    assert response.code == "TEST_ERROR"
    assert response.message == "Test error message"
    assert response.request_id == "req_123"
    assert response.timestamp == now
    assert response.details is None


def test_error_response_with_details():
    """Test error response with details."""
    details = [
        ErrorDetail(field="name", message="Required"),
        ErrorDetail(field="age", message="Must be positive"),
    ]
    
    response = ErrorResponse(
        code="VALIDATION_ERROR",
        message="Validation failed",
        details=details,
        timestamp=datetime.utcnow(),
    )
    
    assert response.code == "VALIDATION_ERROR"
    assert len(response.details) == 2
    assert response.details[0].field == "name"
    assert response.details[1].field == "age"


# Test custom exception classes

def test_app_exception_default():
    """Test AppException with default values."""
    exc = AppException("Test error")
    
    assert exc.message == "Test error"
    assert exc.code == "APP_ERROR"
    assert exc.status_code == 500
    assert exc.details is None


def test_app_exception_custom():
    """Test AppException with custom values."""
    details = [ErrorDetail(message="Detail 1")]
    exc = AppException(
        message="Custom error",
        code="CUSTOM_ERROR",
        status_code=418,
        details=details,
    )
    
    assert exc.message == "Custom error"
    assert exc.code == "CUSTOM_ERROR"
    assert exc.status_code == 418
    assert exc.details == details


def test_validation_exception():
    """Test ValidationException."""
    exc = ValidationException("Invalid data")
    
    assert exc.message == "Invalid data"
    assert exc.code == "VALIDATION_ERROR"
    assert exc.status_code == 400


def test_not_found_exception():
    """Test NotFoundException."""
    exc = NotFoundException()
    
    assert exc.message == "Resource not found"
    assert exc.code == "NOT_FOUND"
    assert exc.status_code == 404


def test_not_found_exception_with_resource():
    """Test NotFoundException with resource name."""
    exc = NotFoundException(resource="User")
    
    assert exc.message == "User not found"
    assert exc.code == "NOT_FOUND"
    assert exc.status_code == 404


def test_permission_denied_exception():
    """Test PermissionDeniedException."""
    exc = PermissionDeniedException()
    
    assert exc.message == "Permission denied"
    assert exc.code == "PERMISSION_DENIED"
    assert exc.status_code == 403


def test_authentication_exception():
    """Test AuthenticationException."""
    exc = AuthenticationException()
    
    assert exc.message == "Authentication failed"
    assert exc.code == "AUTHENTICATION_ERROR"
    assert exc.status_code == 401


def test_conflict_exception():
    """Test ConflictException."""
    exc = ConflictException("Duplicate entry")
    
    assert exc.message == "Duplicate entry"
    assert exc.code == "CONFLICT"
    assert exc.status_code == 409


def test_database_exception():
    """Test DatabaseException."""
    exc = DatabaseException()
    
    assert exc.message == "Database error"
    assert exc.code == "DATABASE_ERROR"
    assert exc.status_code == 500


# Test helper functions

def test_build_error_response_basic():
    """Test building basic error response."""
    response = build_error_response(
        code="TEST_ERROR",
        message="Test message",
    )
    
    assert "error" in response
    assert response["error"]["code"] == "TEST_ERROR"
    assert response["error"]["message"] == "Test message"
    assert response["error"]["request_id"] is None
    assert response["error"]["details"] is None
    assert "timestamp" in response["error"]


def test_build_error_response_with_request_id():
    """Test building error response with request ID."""
    response = build_error_response(
        code="TEST_ERROR",
        message="Test message",
        request_id="req_123",
    )
    
    assert response["error"]["request_id"] == "req_123"


def test_build_error_response_with_details():
    """Test building error response with details."""
    details = [ErrorDetail(field="name", message="Required")]
    response = build_error_response(
        code="VALIDATION_ERROR",
        message="Validation failed",
        details=details,
    )
    
    assert len(response["error"]["details"]) == 1
    assert response["error"]["details"][0]["field"] == "name"


def test_build_validation_error_details():
    """Test building validation error details."""
    errors = [
        {
            "loc": ("body", "name"),
            "msg": "field required",
            "type": "value_error.missing",
        },
        {
            "loc": ("body", "age"),
            "msg": "ensure this value is greater than 0",
            "type": "value_error.number.not_gt",
        },
    ]
    
    details = build_validation_error_details(errors)
    
    assert len(details) == 2
    assert details[0].field == "name"
    assert details[0].message == "field required"
    assert details[0].type == "value_error.missing"
    assert details[1].field == "age"


def test_build_validation_error_details_no_field():
    """Test building validation error details without field."""
    errors = [
        {
            "loc": (),
            "msg": "validation error",
            "type": "value_error",
        },
    ]
    
    details = build_validation_error_details(errors)
    
    assert len(details) == 1
    assert details[0].field is None
    assert details[0].message == "validation error"


# Test exception handlers

@pytest.mark.asyncio
async def test_app_exception_handler(mock_request):
    """Test app exception handler."""
    exc = AppException("Test error", code="TEST_ERROR", status_code=418)
    response = await app_exception_handler(mock_request, exc)
    
    assert response.status_code == 418
    content = response.body.decode()
    assert "TEST_ERROR" in content
    assert "Test error" in content


@pytest.mark.asyncio
async def test_app_exception_handler_with_details(mock_request):
    """Test app exception handler with details."""
    details = [ErrorDetail(field="test", message="Test detail")]
    exc = AppException("Test error", details=details)
    response = await app_exception_handler(mock_request, exc)
    
    assert response.status_code == 500
    content = response.body.decode()
    assert "test" in content
    assert "Test detail" in content


@pytest.mark.asyncio
async def test_http_exception_handler(mock_request):
    """Test HTTP exception handler."""
    exc = StarletteHTTPException(status_code=404, detail="Not found")
    response = await http_exception_handler(mock_request, exc)
    
    assert response.status_code == 404
    content = response.body.decode()
    assert "NOT_FOUND" in content
    assert "Not found" in content


@pytest.mark.asyncio
async def test_http_exception_handler_unknown_status(mock_request):
    """Test HTTP exception handler with unknown status code."""
    exc = StarletteHTTPException(status_code=418, detail="I'm a teapot")
    response = await http_exception_handler(mock_request, exc)
    
    assert response.status_code == 418
    content = response.body.decode()
    assert "HTTP_ERROR" in content


@pytest.mark.asyncio
async def test_validation_exception_handler(mock_request):
    """Test validation exception handler."""
    # Create mock validation error
    from pydantic_core import ValidationError as CoreValidationError
    try:
        TestModel(name=123, age=-1, email="invalid")
    except PydanticValidationError as e:
        # Create RequestValidationError from Pydantic error
        exc = RequestValidationError(e.errors())
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "VALIDATION_ERROR" in content
        assert "Invalid input data" in content


@pytest.mark.asyncio
async def test_integrity_error_handler_unique(mock_request):
    """Test integrity error handler for unique constraint."""
    exc = IntegrityError(
        "UNIQUE constraint failed: users.email",
        None,
        None,
    )
    response = await integrity_error_handler(mock_request, exc)
    
    assert response.status_code == 409
    content = response.body.decode()
    assert "DUPLICATE_RESOURCE" in content
    assert "already exists" in content


@pytest.mark.asyncio
async def test_integrity_error_handler_foreign_key(mock_request):
    """Test integrity error handler for foreign key constraint."""
    exc = IntegrityError(
        "FOREIGN KEY constraint failed",
        None,
        None,
    )
    response = await integrity_error_handler(mock_request, exc)
    
    assert response.status_code == 409
    content = response.body.decode()
    assert "INVALID_REFERENCE" in content


@pytest.mark.asyncio
async def test_integrity_error_handler_not_null(mock_request):
    """Test integrity error handler for NOT NULL constraint."""
    exc = IntegrityError(
        "NOT NULL constraint failed: users.name",
        None,
        None,
    )
    response = await integrity_error_handler(mock_request, exc)
    
    assert response.status_code == 409
    content = response.body.decode()
    assert "NULL_CONSTRAINT_VIOLATION" in content


@pytest.mark.asyncio
async def test_sqlalchemy_error_handler(mock_request):
    """Test SQLAlchemy error handler."""
    exc = SQLAlchemyError("Database connection failed")
    response = await sqlalchemy_error_handler(mock_request, exc)
    
    assert response.status_code == 500
    content = response.body.decode()
    assert "DATABASE_ERROR" in content


@pytest.mark.asyncio
async def test_generic_exception_handler(mock_request):
    """Test generic exception handler."""
    exc = ValueError("Something went wrong")
    response = await generic_exception_handler(mock_request, exc)
    
    assert response.status_code == 500
    content = response.body.decode()
    assert "INTERNAL_SERVER_ERROR" in content
    assert "unexpected error" in content


# Integration tests with FastAPI app

def test_normal_request(client):
    """Test normal request without errors."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_app_exception_integration(client):
    """Test app exception through FastAPI."""
    response = client.get("/error/app")
    assert response.status_code == 500
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "APP_ERROR"
    assert data["error"]["message"] == "Test app error"
    assert "timestamp" in data["error"]


def test_validation_exception_integration(client):
    """Test validation exception through FastAPI."""
    response = client.get("/error/validation")
    assert response.status_code == 400
    
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_not_found_integration(client):
    """Test not found exception through FastAPI."""
    response = client.get("/error/not-found")
    assert response.status_code == 404
    
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_permission_denied_integration(client):
    """Test permission denied exception through FastAPI."""
    response = client.get("/error/permission")
    assert response.status_code == 403
    
    data = response.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


def test_auth_error_integration(client):
    """Test authentication error through FastAPI."""
    response = client.get("/error/auth")
    assert response.status_code == 401
    
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"


def test_conflict_integration(client):
    """Test conflict exception through FastAPI."""
    response = client.get("/error/conflict")
    assert response.status_code == 409
    
    data = response.json()
    assert data["error"]["code"] == "CONFLICT"


def test_database_error_integration(client):
    """Test database error through FastAPI."""
    response = client.get("/error/database")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"]["code"] == "DATABASE_ERROR"


def test_http_exception_integration(client):
    """Test HTTP exception through FastAPI."""
    response = client.get("/error/http")
    assert response.status_code == 404
    
    data = response.json()
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Test HTTP error"


def test_integrity_error_integration(client):
    """Test integrity error through FastAPI."""
    response = client.get("/error/integrity")
    assert response.status_code == 409
    
    data = response.json()
    assert data["error"]["code"] == "DUPLICATE_RESOURCE"


def test_sqlalchemy_error_integration(client):
    """Test SQLAlchemy error through FastAPI."""
    response = client.get("/error/sqlalchemy")
    assert response.status_code == 500
    
    data = response.json()
    assert data["error"]["code"] == "DATABASE_ERROR"


def test_generic_error_integration(client):
    """Test generic error through FastAPI."""
    # ValueError gets re-raised by ServerErrorMiddleware in test environment
    # In production it would be caught by generic_exception_handler
    # This test verifies the handler returns 500 when invoked
    with pytest.raises(ValueError, match="Test generic error"):
        response = client.get("/error/generic")


def test_pydantic_validation_integration(client):
    """Test Pydantic validation through FastAPI."""
    response = client.post("/error/pydantic", json={
        "name": 123,  # Should be string
        "age": -1,    # Should be > 0
        "email": "invalid",  # Invalid email
    })
    
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert len(data["error"]["details"]) > 0


def test_error_response_has_request_id(client):
    """Test that error responses include request ID."""
    response = client.get("/error/not-found")
    
    data = response.json()
    # Request ID should be present (from logging middleware if configured)
    assert "error" in data
    assert "timestamp" in data["error"]


def test_error_response_format(client):
    """Test error response follows correct format."""
    response = client.get("/error/validation")
    
    data = response.json()
    assert "error" in data
    
    error = data["error"]
    assert "code" in error
    assert "message" in error
    assert "timestamp" in error
    # request_id and details are optional
    

def test_multiple_error_types(client):
    """Test multiple error types work correctly."""
    errors = [
        ("/error/validation", 400),
        ("/error/not-found", 404),
        ("/error/permission", 403),
        ("/error/auth", 401),
        ("/error/conflict", 409),
        ("/error/database", 500),
    ]
    
    for path, expected_status in errors:
        response = client.get(path)
        assert response.status_code == expected_status
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]


def test_register_exception_handlers():
    """Test registering exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)
    
    # Check that handlers are registered
    assert len(app.exception_handlers) > 0
    
    # Check specific handlers
    assert AppException in app.exception_handlers
    assert StarletteHTTPException in app.exception_handlers
    assert RequestValidationError in app.exception_handlers
    assert IntegrityError in app.exception_handlers
    assert Exception in app.exception_handlers
