"""
Tests for authentication utilities (password hashing and JWT tokens).
"""
import pytest
from datetime import datetime, timedelta, timezone

from app.utils.auth import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from jose import JWTError


class TestPasswordUtils:
    """Tests for password hashing and verification."""
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test that hash_password creates a bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50  # Bcrypt hashes are typically 60 characters
    
    def test_hash_password_creates_unique_hashes(self):
        """Test that same password generates different hashes (due to salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2  # Different salts produce different hashes
    
    def test_verify_password_with_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "my_secret_password"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_wrong_password(self):
        """Test that verify_password returns False for incorrect password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(correct_password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MyPassword"
        hashed = hash_password(password)
        
        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False
        assert verify_password("MyPassword", hashed) is True


class TestJWTUtils:
    """Tests for JWT token creation and validation."""
    
    def test_create_access_token(self):
        """Test creating an access token."""
        subject = "test-user-123"
        token = create_access_token(subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert "exp" in payload
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        subject = "test-user-456"
        token = create_refresh_token(subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = decode_token(token)
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"
        assert "exp" in payload
    
    def test_access_token_has_correct_expiration(self):
        """Test that access token has correct expiration time."""
        from app.core.config import settings
        
        subject = "test-user"
        token = create_access_token(subject)
        payload = decode_token(token)
        
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 30 minutes (default setting)
        time_diff = (exp_datetime - now).total_seconds()
        expected_seconds = settings.access_token_expire_minutes * 60
        
        # Allow 5 second tolerance
        assert abs(time_diff - expected_seconds) < 5
    
    def test_refresh_token_has_correct_expiration(self):
        """Test that refresh token has correct expiration time."""
        from app.core.config import settings
        
        subject = "test-user"
        token = create_refresh_token(subject)
        payload = decode_token(token)
        
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Should expire in approximately 7 days (default setting)
        time_diff = (exp_datetime - now).total_seconds()
        expected_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
        
        # Allow 5 second tolerance
        assert abs(time_diff - expected_seconds) < 5
    
    def test_decode_token_with_valid_token(self):
        """Test decoding a valid token."""
        subject = "test-user"
        token = create_access_token(subject)
        
        payload = decode_token(token)
        
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert isinstance(payload["exp"], int)
    
    def test_decode_token_with_invalid_token(self):
        """Test that decoding invalid token raises JWTError."""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(JWTError):
            decode_token(invalid_token)
    
    def test_decode_expired_token(self):
        """Test that decoding expired token raises JWTError."""
        subject = "test-user"
        # Create token that expires immediately
        token = create_access_token(subject, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(JWTError):
            decode_token(token)
    
    def test_access_and_refresh_tokens_are_different(self):
        """Test that access and refresh tokens have different types."""
        subject = "test-user"
        access_token = create_access_token(subject)
        refresh_token = create_refresh_token(subject)
        
        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)
        
        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_token != refresh_token
