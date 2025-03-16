"""
Tests for core authentication functionality.

This module contains tests for the core authentication module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta

from netraven.core.auth import (
    get_authorization_header,
    parse_authorization_header,
    validate_api_key,
    validate_jwt_token,
    verify_api_key_dependency,
    create_token,
    validate_token,
    extract_token_from_header,
    has_required_scopes,
    AuthError,
    TOKEN_SECRET_KEY
)

# Test data for new token-based auth tests
TEST_SUBJECT = "test-user"
TEST_SERVICE = "test-service"
TEST_SCOPES = ["read:devices", "write:configs"]

def test_get_authorization_header():
    """Test that the authorization header is correctly generated."""
    api_key = "test-api-key"
    header = get_authorization_header(api_key)
    
    assert header == {"Authorization": "Bearer test-api-key"}

def test_parse_authorization_header_valid():
    """Test that a valid authorization header is correctly parsed."""
    authorization = "Bearer test-token"
    is_valid, token = parse_authorization_header(authorization)
    
    assert is_valid is True
    assert token == "test-token"

def test_parse_authorization_header_invalid_format():
    """Test that an invalid authorization header format is correctly identified."""
    authorization = "Basic test-token"
    is_valid, token = parse_authorization_header(authorization)
    
    assert is_valid is False
    assert token is None

def test_parse_authorization_header_missing():
    """Test that a missing authorization header is correctly handled."""
    is_valid, token = parse_authorization_header(None)
    
    assert is_valid is False
    assert token is None

def test_validate_api_key_valid():
    """Test that a valid API key is correctly validated."""
    authorization = "Bearer test-api-key"
    expected_api_key = "test-api-key"
    
    with patch("netraven.core.auth.logger") as mock_logger:
        result = validate_api_key(authorization, expected_api_key, "test-service")
    
    assert result is True
    mock_logger.debug.assert_called_once()

def test_validate_api_key_invalid():
    """Test that an invalid API key is correctly rejected."""
    authorization = "Bearer wrong-api-key"
    expected_api_key = "test-api-key"
    
    with patch("netraven.core.auth.logger") as mock_logger:
        result = validate_api_key(authorization, expected_api_key, "test-service")
    
    assert result is False
    mock_logger.warning.assert_called_once()

def test_validate_api_key_missing():
    """Test that a missing API key is correctly handled."""
    authorization = None
    expected_api_key = "test-api-key"
    
    with patch("netraven.core.auth.logger") as mock_logger:
        result = validate_api_key(authorization, expected_api_key, "test-service")
    
    assert result is False
    mock_logger.warning.assert_called_once()

def test_validate_jwt_token_valid():
    """Test that a valid JWT token is correctly validated."""
    # Using a known test token with payload {"sub": "test-user"}
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIifQ.FPYh8P3FNZkCl_NHqRRcIKIJKR3UEOvEwl6UR47pUCs"
    authorization = f"Bearer {test_token}"
    jwt_secret = "test-secret"
    
    with patch("netraven.core.auth.jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": "test-user"}
        payload = validate_jwt_token(authorization, jwt_secret, ["HS256"], "test-service")
    
    assert payload == {"sub": "test-user"}
    mock_decode.assert_called_once_with(test_token, jwt_secret, algorithms=["HS256"])

def test_validate_jwt_token_invalid():
    """Test that an invalid JWT token is correctly rejected."""
    authorization = "Bearer invalid-token"
    jwt_secret = "test-secret"
    
    with patch("netraven.core.auth.jwt.decode") as mock_decode:
        mock_decode.side_effect = Exception("Invalid token")
        payload = validate_jwt_token(authorization, jwt_secret, ["HS256"], "test-service")
    
    assert payload is None
    mock_decode.assert_called_once()

@pytest.mark.asyncio
async def test_verify_api_key_dependency_bearer():
    """Test that the API key dependency works with Bearer authentication."""
    authorization = "Bearer test-api-key"
    
    with patch("netraven.core.auth.os.environ.get") as mock_get:
        mock_get.return_value = "test-api-key"
        result = await verify_api_key_dependency(
            authorization=authorization,
            x_api_key=None,
            api_key_env_var="TEST_API_KEY",
            service_name="test-service"
        )
    
    assert result == {"type": "api_key", "method": "bearer"}
    mock_get.assert_called_once_with("TEST_API_KEY", "")

@pytest.mark.asyncio
async def test_verify_api_key_dependency_x_api_key():
    """Test that the API key dependency works with X-API-Key header."""
    x_api_key = "test-api-key"
    
    with patch("netraven.core.auth.os.environ.get") as mock_get:
        mock_get.return_value = "test-api-key"
        result = await verify_api_key_dependency(
            authorization=None,
            x_api_key=x_api_key,
            api_key_env_var="TEST_API_KEY",
            service_name="test-service"
        )
    
    assert result == {"type": "api_key", "method": "x-api-key"}
    mock_get.assert_called_once_with("TEST_API_KEY", "")

@pytest.mark.asyncio
async def test_verify_api_key_dependency_invalid():
    """Test that the API key dependency rejects invalid authentication."""
    authorization = "Bearer wrong-api-key"
    
    with patch("netraven.core.auth.os.environ.get") as mock_get:
        mock_get.return_value = "test-api-key"
        with pytest.raises(HTTPException) as excinfo:
            await verify_api_key_dependency(
                authorization=authorization,
                x_api_key=None,
                api_key_env_var="TEST_API_KEY",
                service_name="test-service"
            )
    
    assert excinfo.value.status_code == 401
    mock_get.assert_called_once_with("TEST_API_KEY", "")

def test_create_token_user():
    """Test creating a user token with expiration."""
    token = create_token(
        subject=TEST_SUBJECT,
        token_type="user",
        scopes=TEST_SCOPES,
        expiration=timedelta(minutes=5)
    )
    
    # Verify token is a string
    assert isinstance(token, str)
    
    # Decode and verify contents
    payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == TEST_SUBJECT
    assert payload["type"] == "user"
    assert set(payload["scope"]) == set(TEST_SCOPES)
    assert "exp" in payload
    assert "iat" in payload
    assert "jti" in payload

def test_create_token_service():
    """Test creating a service token without expiration."""
    token = create_token(
        subject=TEST_SERVICE,
        token_type="service",
        scopes=TEST_SCOPES
    )
    
    # Verify token is a string
    assert isinstance(token, str)
    
    # Decode and verify contents
    payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == TEST_SERVICE
    assert payload["type"] == "service"
    assert set(payload["scope"]) == set(TEST_SCOPES)
    assert "exp" not in payload
    assert "iat" in payload
    assert "jti" in payload

def test_validate_token_success():
    """Test successful token validation."""
    token = create_token(
        subject=TEST_SUBJECT,
        token_type="user",
        scopes=TEST_SCOPES,
        expiration=timedelta(minutes=5)
    )
    
    # Validate token
    payload = validate_token(token)
    assert payload["sub"] == TEST_SUBJECT
    assert payload["type"] == "user"
    assert set(payload["scope"]) == set(TEST_SCOPES)

def test_validate_token_expired():
    """Test validation of expired token."""
    # Create token that's already expired
    exp_time = datetime.utcnow() - timedelta(minutes=5)
    payload = {
        "sub": TEST_SUBJECT,
        "type": "user",
        "scope": TEST_SCOPES,
        "exp": exp_time.timestamp(),
        "iat": exp_time.timestamp() - 300,
        "jti": "test-id"
    }
    token = jwt.encode(payload, TOKEN_SECRET_KEY, algorithm="HS256")
    
    # Validation should fail with AuthError
    with pytest.raises(AuthError):
        validate_token(token)

def test_validate_token_invalid():
    """Test validation of invalid token."""
    # Create token with wrong signature
    token = jwt.encode(
        {
            "sub": TEST_SUBJECT,
            "type": "user",
            "scope": TEST_SCOPES,
            "iat": datetime.utcnow().timestamp(),
            "jti": "test-id"
        },
        "wrong-secret-key",
        algorithm="HS256"
    )
    
    # Validation should fail with AuthError
    with pytest.raises(AuthError):
        validate_token(token)

def test_validate_token_with_scopes():
    """Test token validation with scope checking."""
    token = create_token(
        subject=TEST_SUBJECT,
        token_type="user",
        scopes=["read:devices", "write:configs"],
        expiration=timedelta(minutes=5)
    )
    
    # Validate with subset of scopes
    payload = validate_token(token, required_scopes=["read:devices"])
    assert payload["sub"] == TEST_SUBJECT
    
    # Validate with exact scopes
    payload = validate_token(token, required_scopes=["read:devices", "write:configs"])
    assert payload["sub"] == TEST_SUBJECT
    
    # Validation should fail with missing scope
    with pytest.raises(AuthError):
        validate_token(token, required_scopes=["admin:users"])

def test_has_required_scopes():
    """Test scope checking functionality."""
    # Basic scope matching
    assert has_required_scopes(["read:devices"], ["read:devices"])
    assert has_required_scopes(["read:devices", "write:configs"], ["read:devices"])
    assert not has_required_scopes(["read:devices"], ["write:configs"])
    
    # Wildcard scope
    assert has_required_scopes(["*"], ["read:devices", "admin:users"])
    
    # Prefix wildcards
    assert has_required_scopes(["read:*"], ["read:devices"])
    assert has_required_scopes(["read:*", "write:*"], ["read:devices", "write:configs"])
    assert not has_required_scopes(["read:*"], ["admin:users"])

def test_extract_token_from_header():
    """Test token extraction from Authorization header."""
    # Valid header
    token = extract_token_from_header("Bearer test-token")
    assert token == "test-token"
    
    # Invalid headers
    assert extract_token_from_header(None) is None
    assert extract_token_from_header("") is None
    assert extract_token_from_header("Basic dXNlcjpwYXNz") is None
    assert extract_token_from_header("Bearer") is None 