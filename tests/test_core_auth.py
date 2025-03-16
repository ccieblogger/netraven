"""
Tests for core authentication functionality.

This module contains tests for the core authentication module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from netraven.core.auth import (
    get_authorization_header,
    parse_authorization_header,
    validate_api_key,
    validate_jwt_token,
    verify_api_key_dependency
)

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