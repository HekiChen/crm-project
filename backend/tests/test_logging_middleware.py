"""
Tests for logging middleware.
"""
import pytest
import json
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.logging import (
    generate_request_id,
    sanitize_data,
    sanitize_headers,
    get_request_id,
    log_event,
    log_database_query,
    log_security_event,
    LoggingMiddleware,
    SENSITIVE_FIELDS,
)


class TestRequestID:
    """Test cases for request ID generation."""
    
    def test_generate_request_id(self):
        """Test request ID generation."""
        request_id = generate_request_id()
        
        assert isinstance(request_id, str)
        assert request_id.startswith("req_")
        assert len(request_id) == 16  # req_ + 12 hex chars
    
    def test_unique_request_ids(self):
        """Test that request IDs are unique."""
        ids = [generate_request_id() for _ in range(100)]
        
        # All should be unique
        assert len(set(ids)) == 100


class TestDataSanitization:
    """Test cases for data sanitization."""
    
    def test_sanitize_password(self):
        """Test sanitizing password field."""
        data = {"username": "user", "password": "secret123"}
        sanitized = sanitize_data(data)
        
        assert sanitized["username"] == "user"
        assert sanitized["password"] == "***REDACTED***"
    
    def test_sanitize_token(self):
        """Test sanitizing token field."""
        data = {"user_id": 123, "access_token": "abc123"}
        sanitized = sanitize_data(data)
        
        assert sanitized["user_id"] == 123
        assert sanitized["access_token"] == "***REDACTED***"
    
    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "password": "secret",
            },
            "metadata": {
                "api_key": "key123",
            }
        }
        sanitized = sanitize_data(data)
        
        assert sanitized["user"]["name"] == "John"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["metadata"]["api_key"] == "***REDACTED***"
    
    def test_sanitize_list_of_dicts(self):
        """Test sanitizing list of dictionaries."""
        data = {
            "users": [
                {"name": "Alice", "password": "pass1"},
                {"name": "Bob", "password": "pass2"},
            ]
        }
        sanitized = sanitize_data(data)
        
        assert sanitized["users"][0]["name"] == "Alice"
        assert sanitized["users"][0]["password"] == "***REDACTED***"
        assert sanitized["users"][1]["name"] == "Bob"
        assert sanitized["users"][1]["password"] == "***REDACTED***"
    
    def test_sanitize_case_insensitive(self):
        """Test case-insensitive sanitization."""
        data = {
            "PASSWORD": "secret",
            "Password": "secret",
            "PaSsWoRd": "secret",
        }
        sanitized = sanitize_data(data)
        
        assert sanitized["PASSWORD"] == "***REDACTED***"
        assert sanitized["Password"] == "***REDACTED***"
        assert sanitized["PaSsWoRd"] == "***REDACTED***"
    
    def test_sanitize_partial_match(self):
        """Test sanitizing fields with partial matches."""
        data = {
            "user_password": "secret",
            "refresh_token": "token123",
            "api_key_secret": "key",
        }
        sanitized = sanitize_data(data)
        
        assert sanitized["user_password"] == "***REDACTED***"
        assert sanitized["refresh_token"] == "***REDACTED***"
        assert sanitized["api_key_secret"] == "***REDACTED***"
    
    def test_sanitize_custom_fields(self):
        """Test sanitizing with custom sensitive fields."""
        data = {
            "username": "user",
            "ssn": "123-45-6789",
            "credit_card": "1234-5678-9012-3456",
        }
        
        custom_fields = {"ssn", "credit_card"}
        sanitized = sanitize_data(data, custom_fields)
        
        assert sanitized["username"] == "user"
        assert sanitized["ssn"] == "***REDACTED***"
        assert sanitized["credit_card"] == "***REDACTED***"
    
    def test_sanitize_headers(self):
        """Test sanitizing HTTP headers."""
        headers = {
            "content-type": "application/json",
            "authorization": "Bearer token123",
            "cookie": "session=abc123",
        }
        
        sanitized = sanitize_headers(headers)
        
        assert sanitized["content-type"] == "application/json"
        assert sanitized["authorization"] == "***REDACTED***"
        assert sanitized["cookie"] == "***REDACTED***"


class TestLoggingMiddleware:
    """Test cases for logging middleware."""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app with logging middleware."""
        app = FastAPI()
        
        app.add_middleware(LoggingMiddleware, slow_request_threshold=0.1)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.get("/slow")
        async def slow_endpoint():
            import time
            time.sleep(0.2)
            return {"message": "slow"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)
    
    @patch('app.middleware.logging.logger')
    def test_request_logging(self, mock_logger, client):
        """Test that requests are logged."""
        response = client.get("/test")
        
        assert response.status_code == 200
        
        # Check that logger was called
        assert mock_logger.info.called
        
        # Get logged data
        calls = mock_logger.info.call_args_list
        assert len(calls) >= 2  # Request and response logs
    
    @patch('app.middleware.logging.logger')
    def test_request_id_in_logs(self, mock_logger, client):
        """Test that request ID is present in logs."""
        response = client.get("/test")
        
        # Get request log
        request_log_str = mock_logger.info.call_args_list[0][0][0]
        request_log = json.loads(request_log_str)
        
        assert "request_id" in request_log
        assert request_log["request_id"].startswith("req_")
    
    def test_request_id_in_response_header(self, client):
        """Test that request ID is added to response headers."""
        response = client.get("/test")
        
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("req_")
    
    @patch('app.middleware.logging.logger')
    def test_slow_request_warning(self, mock_logger, client):
        """Test that slow requests are logged as warnings."""
        response = client.get("/slow")
        
        assert response.status_code == 200
        
        # Check that warning was logged
        assert mock_logger.warning.called
    
    @patch('app.middleware.logging.logger')
    def test_error_logging(self, mock_logger, client):
        """Test that errors are logged."""
        with pytest.raises(ValueError):
            client.get("/error")
        
        # Check that error was logged
        assert mock_logger.error.called
    
    @patch('app.middleware.logging.logger')
    def test_log_format(self, mock_logger, client):
        """Test that logs are in JSON format."""
        response = client.get("/test")
        
        # Get first log call
        log_str = mock_logger.info.call_args_list[0][0][0]
        log_data = json.loads(log_str)
        
        # Verify structure
        assert "timestamp" in log_data
        assert "type" in log_data
        assert "request_id" in log_data
        assert "method" in log_data
        assert "path" in log_data


class TestLogHelpers:
    """Test cases for log helper functions."""
    
    @patch('app.middleware.logging.logger')
    def test_log_event(self, mock_logger):
        """Test log_event function."""
        log_event(
            request_id="req_123",
            event_type="custom_event",
            message="Test message",
            extra_field="value",
        )
        
        assert mock_logger.info.called
        
        # Verify log format
        log_str = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_str)
        
        assert log_data["request_id"] == "req_123"
        assert log_data["type"] == "custom_event"
        assert log_data["message"] == "Test message"
        assert log_data["extra_field"] == "value"
    
    @patch('app.middleware.logging.logger')
    def test_log_database_query_normal(self, mock_logger):
        """Test logging normal database query."""
        log_database_query(
            request_id="req_123",
            query="SELECT * FROM users",
            duration_ms=50.0,
        )
        
        # Should use debug level for normal queries
        assert mock_logger.debug.called
    
    @patch('app.middleware.logging.logger')
    def test_log_database_query_slow(self, mock_logger):
        """Test logging slow database query."""
        log_database_query(
            request_id="req_123",
            query="SELECT * FROM users",
            duration_ms=150.0,
            slow_query_threshold=100.0,
        )
        
        # Should use warning level for slow queries
        assert mock_logger.warning.called
        
        # Verify slow_query flag
        log_str = mock_logger.warning.call_args[0][0]
        log_data = json.loads(log_str)
        
        assert log_data["slow_query"] is True
    
    @patch('app.middleware.logging.logger')
    def test_log_security_event_low(self, mock_logger):
        """Test logging low severity security event."""
        log_security_event(
            request_id="req_123",
            event="User login attempt",
            severity="low",
            user_id="user_123",
        )
        
        assert mock_logger.info.called
    
    @patch('app.middleware.logging.logger')
    def test_log_security_event_high(self, mock_logger):
        """Test logging high severity security event."""
        log_security_event(
            request_id="req_123",
            event="Multiple failed login attempts",
            severity="high",
            user_id="user_123",
        )
        
        assert mock_logger.error.called
    
    @patch('app.middleware.logging.logger')
    def test_log_security_event_critical(self, mock_logger):
        """Test logging critical security event."""
        log_security_event(
            request_id="req_123",
            event="Potential SQL injection detected",
            severity="critical",
        )
        
        assert mock_logger.error.called


class TestGetRequestID:
    """Test cases for getting request ID."""
    
    def test_get_request_id_present(self):
        """Test getting request ID when present."""
        request = Mock(spec=Request)
        request.state.request_id = "req_123"
        
        request_id = get_request_id(request)
        
        assert request_id == "req_123"
    
    def test_get_request_id_missing(self):
        """Test getting request ID when not present."""
        request = Mock(spec=Request)
        request.state = Mock()
        del request.state.request_id  # Ensure it doesn't exist
        
        request_id = get_request_id(request)
        
        assert request_id is None
