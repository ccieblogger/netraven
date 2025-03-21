"""
Unit tests for authentication extensions.

These tests verify the authentication extensions, including:
- Token refresh mechanism
- Token validation with scopes
- Permission-based access control
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from jose import jwt, JWTError

from netraven.web.auth.jwt import (
    create_access_token,
    create_refresh_token,
    refresh_access_token,
    decode_token,
    get_current_user,
    get_current_user_with_scopes
)


@pytest.fixture
def test_user_data():
    """Sample user data for testing authentication."""
    return {
        "sub": "test-user",
        "roles": ["user"],
        "email": "test@example.com"
    }


@pytest.fixture
def admin_user_data():
    """Sample admin user data for testing authentication."""
    return {
        "sub": "admin-user",
        "roles": ["admin", "user"],
        "email": "admin@example.com"
    }


class TestTokenGeneration:
    """Tests for token generation functions."""
    
    def test_create_access_token(self, test_user_data):
        """Test creation of access tokens."""
        # Create token with default expiry
        token = create_access_token(data=test_user_data)
        
        # Verify token was created
        assert token is not None
        assert isinstance(token, str)
        
        # Decode token and verify claims
        payload = jwt.decode(
            token,
            "test-secret-key",  # This should be mocked in actual implementation
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == test_user_data["sub"]
        assert payload["roles"] == test_user_data["roles"]
        assert "exp" in payload
        
        # Verify no scopes by default
        assert "scopes" not in payload or not payload["scopes"]
        
        # Create token with custom expiry
        short_token = create_access_token(
            data=test_user_data,
            expires_minutes=5
        )
        
        # Decode and verify expiry
        short_payload = jwt.decode(
            short_token,
            "test-secret-key",
            algorithms=["HS256"]
        )
        
        # Expiry should be about 5 minutes from now
        exp_time = datetime.fromtimestamp(short_payload["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now
        
        # Allow 5 seconds tolerance for test execution time
        assert abs(time_diff.total_seconds() - 300) < 5
        
        # Create token with scopes
        scoped_token = create_access_token(
            data=test_user_data,
            scopes=["read:devices", "write:devices"]
        )
        
        # Decode and verify scopes
        scoped_payload = jwt.decode(
            scoped_token,
            "test-secret-key",
            algorithms=["HS256"]
        )
        
        assert "scopes" in scoped_payload
        assert "read:devices" in scoped_payload["scopes"]
        assert "write:devices" in scoped_payload["scopes"]
    
    def test_create_refresh_token(self, test_user_data):
        """Test creation of refresh tokens."""
        # Create refresh token
        token = create_refresh_token(data=test_user_data)
        
        # Verify token was created
        assert token is not None
        assert isinstance(token, str)
        
        # Decode token and verify claims
        payload = jwt.decode(
            token,
            "test-refresh-secret-key",  # This should be mocked in actual implementation
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == test_user_data["sub"]
        assert "token_type" in payload and payload["token_type"] == "refresh"
        assert "exp" in payload
        
        # Refresh tokens should have longer expiry than access tokens
        # Default is 7 days for refresh vs 30 minutes for access
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now
        
        # Should be close to 7 days (with 5 minute tolerance)
        assert abs(time_diff.total_seconds() - (7 * 24 * 60 * 60)) < 300
        
        # Create token with custom expiry
        short_token = create_refresh_token(
            data=test_user_data,
            expires_days=1
        )
        
        # Decode and verify expiry
        short_payload = jwt.decode(
            short_token,
            "test-refresh-secret-key",
            algorithms=["HS256"]
        )
        
        # Expiry should be about 1 day from now
        exp_time = datetime.fromtimestamp(short_payload["exp"])
        time_diff = exp_time - now
        
        # Allow 5 minute tolerance
        assert abs(time_diff.total_seconds() - (24 * 60 * 60)) < 300


class TestTokenRefresh:
    """Tests for token refresh functionality."""
    
    def test_refresh_access_token(self, test_user_data):
        """Test refreshing an access token using a refresh token."""
        # Create a refresh token
        refresh_token = create_refresh_token(data=test_user_data)
        
        # Refresh to get a new access token
        access_token = refresh_access_token(refresh_token)
        
        # Verify new access token
        assert access_token is not None
        assert isinstance(access_token, str)
        
        # Decode and verify
        payload = jwt.decode(
            access_token,
            "test-secret-key",
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == test_user_data["sub"]
        assert "exp" in payload
        
        # Try with expired refresh token
        with patch("netraven.web.auth.jwt.decode_token") as mock_decode:
            # Simulate an expired token
            mock_decode.side_effect = JWTError("Token expired")
            
            # Attempt to refresh with expired token
            with pytest.raises(JWTError):
                refresh_access_token("expired-token")
    
    def test_refresh_token_validation(self):
        """Test validation of refresh tokens."""
        # Create an invalid token format
        invalid_token = "not-a-valid-token"
        
        # Attempt to refresh with invalid token
        with pytest.raises(JWTError):
            refresh_access_token(invalid_token)
        
        # Create a token with wrong type (access instead of refresh)
        wrong_type_token = create_access_token(data={"sub": "user"})
        
        # Attempt to refresh with wrong token type
        with pytest.raises(ValueError, match="Not a refresh token"):
            refresh_access_token(wrong_type_token)
        
        # Create a tampered token
        tampered_token = jwt.encode(
            {
                "sub": "hacker",
                "token_type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=7)
            },
            "wrong-secret-key",
            algorithm="HS256"
        )
        
        # Attempt to refresh with tampered token
        with pytest.raises(JWTError):
            refresh_access_token(tampered_token)


class TestTokenDecoding:
    """Tests for token decoding and validation."""
    
    def test_decode_token(self, test_user_data):
        """Test decoding tokens."""
        # Create an access token
        token = create_access_token(data=test_user_data)
        
        # Decode token
        payload = decode_token(token)
        
        # Verify payload
        assert payload is not None
        assert payload["sub"] == test_user_data["sub"]
        assert payload["roles"] == test_user_data["roles"]
        
        # Test with invalid token
        with pytest.raises(JWTError):
            decode_token("invalid-token")
        
        # Test with expired token
        with patch("jose.jwt.decode") as mock_decode:
            mock_decode.side_effect = JWTError("Token expired")
            with pytest.raises(JWTError):
                decode_token(token)


class TestUserAuthorization:
    """Tests for user authorization functions."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        mock = MagicMock()
        
        # Configure mock to return user objects
        def get_user_by_username(username):
            if username == "test-user":
                return MagicMock(
                    id="user-id",
                    username="test-user",
                    email="test@example.com",
                    is_active=True,
                    is_admin=False
                )
            elif username == "admin-user":
                return MagicMock(
                    id="admin-id",
                    username="admin-user",
                    email="admin@example.com",
                    is_active=True,
                    is_admin=True
                )
            return None
        
        mock.query().filter().first.side_effect = get_user_by_username
        return mock
    
    def test_get_current_user(self, test_user_data, mock_db):
        """Test retrieving the current user from a token."""
        # Create an access token
        token = create_access_token(data=test_user_data)
        
        # Get current user
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            user = get_current_user(token, db=mock_db)
            
            # Verify user
            assert user is not None
            assert user.username == "test-user"
            assert user.is_active is True
            assert user.is_admin is False
    
    def test_get_current_user_inactive(self, mock_db):
        """Test retrieving an inactive user."""
        # Create token for inactive user
        token = create_access_token(data={"sub": "inactive-user"})
        
        # Configure mock to return inactive user
        mock_db.query().filter().first.return_value = MagicMock(
            username="inactive-user",
            is_active=False
        )
        
        # Attempt to get current user
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            with pytest.raises(ValueError, match="Inactive user"):
                get_current_user(token, db=mock_db)
    
    def test_get_current_user_not_found(self, mock_db):
        """Test retrieving a non-existent user."""
        # Create token for non-existent user
        token = create_access_token(data={"sub": "nonexistent-user"})
        
        # Configure mock to return no user
        mock_db.query().filter().first.return_value = None
        
        # Attempt to get current user
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            with pytest.raises(ValueError, match="User not found"):
                get_current_user(token, db=mock_db)
    
    def test_get_current_user_with_scopes(self, admin_user_data, mock_db):
        """Test retrieving user with scope verification."""
        # Create token with admin scopes
        token = create_access_token(
            data=admin_user_data,
            scopes=["admin:read", "admin:write"]
        )
        
        # Get user with scope verification
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            # Create dependency with required scopes
            user_dependency = get_current_user_with_scopes(["admin:read"])
            
            # Call dependency with token
            user = user_dependency(token=token, db=mock_db)
            
            # Verify user
            assert user is not None
            assert user.username == "admin-user"
            assert user.is_admin is True
    
    def test_get_current_user_insufficient_scopes(self, test_user_data, mock_db):
        """Test retrieving user with insufficient scopes."""
        # Create token with limited scopes
        token = create_access_token(
            data=test_user_data,
            scopes=["user:read"]
        )
        
        # Try to get user with admin scope verification
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            # Create dependency with required admin scopes
            user_dependency = get_current_user_with_scopes(["admin:read"])
            
            # Call dependency with token that has insufficient scopes
            with pytest.raises(ValueError, match="Insufficient scopes"):
                user_dependency(token=token, db=mock_db)
    
    def test_get_current_user_role_based_scopes(self, test_user_data, admin_user_data, mock_db):
        """Test role-based scope verification."""
        # Create user token with no explicit scopes
        user_token = create_access_token(data=test_user_data)
        
        # Create admin token with no explicit scopes
        admin_token = create_access_token(data=admin_user_data)
        
        with patch("netraven.web.auth.jwt.get_db", return_value=mock_db):
            # Create dependency with admin scope
            admin_dependency = get_current_user_with_scopes(["admin:settings"])
            
            # Regular user should not have access
            with pytest.raises(ValueError, match="Insufficient scopes"):
                admin_dependency(token=user_token, db=mock_db)
            
            # Admin user should have access even without explicit scopes
            admin_user = admin_dependency(token=admin_token, db=mock_db)
            assert admin_user is not None
            assert admin_user.username == "admin-user" 