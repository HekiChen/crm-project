"""
Tests for authentication middleware.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException

from app.middleware.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    blacklist_token,
    is_token_blacklisted,
    TokenData,
    TokenPair,
    CurrentUser,
    token_blacklist,
)


class TestPasswordHashing:
    """Test cases for password hashing functions."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt prefix
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (salt)."""
        password = "test_password"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Different hashes due to random salt
        assert hash1 != hash2
        # But both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenCreation:
    """Test cases for token creation functions."""
    
    def test_create_access_token(self):
        """Test creating access token."""
        user_id = uuid4()
        username = "testuser"
        
        token = create_access_token(user_id, username)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_id = uuid4()
        username = "testuser"
        
        token = create_refresh_token(user_id, username)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_pair(self):
        """Test creating token pair."""
        user_id = uuid4()
        username = "testuser"
        
        pair = create_token_pair(user_id, username)
        
        assert isinstance(pair, TokenPair)
        assert isinstance(pair.access_token, str)
        assert isinstance(pair.refresh_token, str)
        assert pair.token_type == "bearer"
        assert pair.access_token != pair.refresh_token
    
    def test_access_token_custom_expiration(self):
        """Test access token with custom expiration."""
        user_id = uuid4()
        username = "testuser"
        expires_delta = timedelta(minutes=5)
        
        token = create_access_token(user_id, username, expires_delta)
        
        assert isinstance(token, str)
        
        # Decode and check expiration
        token_data = decode_token(token)
        expected_exp = datetime.utcnow() + expires_delta
        
        # Allow 2 second difference for processing time
        assert abs((token_data.exp - expected_exp).total_seconds()) < 2


class TestTokenDecoding:
    """Test cases for token decoding."""
    
    def test_decode_valid_token(self):
        """Test decoding valid token."""
        user_id = uuid4()
        username = "testuser"
        
        token = create_access_token(user_id, username)
        token_data = decode_token(token)
        
        assert isinstance(token_data, TokenData)
        assert token_data.user_id == user_id
        assert token_data.username == username
        assert isinstance(token_data.exp, datetime)
    
    def test_decode_expired_token(self):
        """Test decoding expired token."""
        user_id = uuid4()
        username = "testuser"
        
        # Create token that expires immediately
        token = create_access_token(user_id, username, timedelta(seconds=-1))
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid_token")
        
        assert exc_info.value.status_code == 401
    
    def test_decode_malformed_token(self):
        """Test decoding malformed token."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.real.jwt.token")
        
        assert exc_info.value.status_code == 401


class TestTokenBlacklist:
    """Test cases for token blacklist."""
    
    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()
    
    def test_blacklist_token(self):
        """Test adding token to blacklist."""
        token = "test_token_123"
        
        blacklist_token(token)
        
        assert is_token_blacklisted(token) is True
    
    def test_non_blacklisted_token(self):
        """Test checking non-blacklisted token."""
        token = "test_token_123"
        
        assert is_token_blacklisted(token) is False
    
    def test_multiple_blacklisted_tokens(self):
        """Test multiple tokens in blacklist."""
        token1 = "token_1"
        token2 = "token_2"
        token3 = "token_3"
        
        blacklist_token(token1)
        blacklist_token(token2)
        
        assert is_token_blacklisted(token1) is True
        assert is_token_blacklisted(token2) is True
        assert is_token_blacklisted(token3) is False


class TestCurrentUser:
    """Test cases for CurrentUser model."""
    
    def test_current_user_creation(self):
        """Test creating CurrentUser."""
        user_id = uuid4()
        
        user = CurrentUser(
            id=user_id,
            username="testuser",
            email="test@example.com",
        )
        
        assert user.id == user_id
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_current_user_with_flags(self):
        """Test creating CurrentUser with custom flags."""
        user = CurrentUser(
            id=uuid4(),
            username="admin",
            email="admin@example.com",
            is_active=False,
            is_superuser=True,
        )
        
        assert user.is_active is False
        assert user.is_superuser is True


class TestTokenPair:
    """Test cases for TokenPair model."""
    
    def test_token_pair_creation(self):
        """Test creating TokenPair."""
        pair = TokenPair(
            access_token="access_123",
            refresh_token="refresh_456",
        )
        
        assert pair.access_token == "access_123"
        assert pair.refresh_token == "refresh_456"
        assert pair.token_type == "bearer"
    
    def test_token_pair_custom_type(self):
        """Test TokenPair with custom token type."""
        pair = TokenPair(
            access_token="access",
            refresh_token="refresh",
            token_type="custom",
        )
        
        assert pair.token_type == "custom"


class TestAuthenticationFlow:
    """Test cases for complete authentication flow."""
    
    def setup_method(self):
        """Clear blacklist before each test."""
        token_blacklist.clear()
    
    def test_full_authentication_flow(self):
        """Test complete auth flow: hash password, create tokens, decode."""
        # 1. Hash password
        password = "user_password_123"
        hashed_password = get_password_hash(password)
        
        # 2. Verify password
        assert verify_password(password, hashed_password) is True
        
        # 3. Create tokens
        user_id = uuid4()
        username = "testuser"
        token_pair = create_token_pair(user_id, username)
        
        # 4. Decode access token
        token_data = decode_token(token_pair.access_token)
        assert token_data.user_id == user_id
        assert token_data.username == username
        
        # 5. Decode refresh token
        refresh_data = decode_token(token_pair.refresh_token)
        assert refresh_data.user_id == user_id
    
    def test_logout_flow(self):
        """Test logout flow with token blacklist."""
        # Create tokens
        user_id = uuid4()
        username = "testuser"
        token_pair = create_token_pair(user_id, username)
        
        # Token should work initially
        token_data = decode_token(token_pair.access_token)
        assert token_data.user_id == user_id
        
        # Blacklist token (logout)
        blacklist_token(token_pair.access_token)
        
        # Token should now be blacklisted
        assert is_token_blacklisted(token_pair.access_token) is True
        
        # Can still decode, but should check blacklist before use
        token_data = decode_token(token_pair.access_token)
        assert token_data.user_id == user_id
    
    def test_token_refresh_flow(self):
        """Test token refresh flow."""
        # Create initial token pair
        user_id = uuid4()
        username = "testuser"
        old_pair = create_token_pair(user_id, username)
        
        # Blacklist old access token
        blacklist_token(old_pair.access_token)
        
        # Decode refresh token to get user info
        refresh_data = decode_token(old_pair.refresh_token)
        
        # Create new token pair
        new_pair = create_token_pair(refresh_data.user_id, refresh_data.username)
        
        # Old access token should be blacklisted
        assert is_token_blacklisted(old_pair.access_token) is True
        
        # New access token should work
        new_data = decode_token(new_pair.access_token)
        assert new_data.user_id == user_id
        assert is_token_blacklisted(new_pair.access_token) is False


class TestAuthorizationLevels:
    """Test cases for different authorization levels."""
    
    def test_regular_user(self):
        """Test regular user permissions."""
        user = CurrentUser(
            id=uuid4(),
            username="user",
            email="user@example.com",
            is_active=True,
            is_superuser=False,
        )
        
        assert user.is_active is True
        assert user.is_superuser is False
    
    def test_inactive_user(self):
        """Test inactive user."""
        user = CurrentUser(
            id=uuid4(),
            username="inactive",
            email="inactive@example.com",
            is_active=False,
            is_superuser=False,
        )
        
        assert user.is_active is False
    
    def test_superuser(self):
        """Test superuser permissions."""
        user = CurrentUser(
            id=uuid4(),
            username="admin",
            email="admin@example.com",
            is_active=True,
            is_superuser=True,
        )
        
        assert user.is_active is True
        assert user.is_superuser is True
