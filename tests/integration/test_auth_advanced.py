"""
Integration tests for advanced authentication features.

This module tests advanced authentication features including:
- Token refresh flow
- Token scopes and permissions
- Authentication event logging
- Session management
"""

import pytest
import requests
import uuid
import json
import time
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

from httpx import AsyncClient # Use httpx for async requests
import jwt # To decode tokens for inspection

from tests.utils.api_test_utils import create_auth_headers, create_test_api_token
from netraven.core.config import settings # For token secret


def test_service_token_generation(app_config, admin_token):
    """Test service token generation endpoint."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Create a service token request
    service_name = f"test-service-{uuid.uuid4().hex[:8]}"
    service_token_data = {
        "service_name": service_name,
        "scopes": ["read:devices", "read:backups"],
        "expiration_days": 30
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=service_token_data
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response data structure
    token_response = response.json()
    assert "access_token" in token_response, "Response missing 'access_token' field"
    assert "token_type" in token_response, "Response missing 'token_type' field"
    assert "expires_in" in token_response, "Response missing 'expires_in' field"
    
    # Verify the token works
    service_token = token_response["access_token"]
    service_headers = create_auth_headers(service_token)
    
    # Test that the token can access devices (read:devices scope)
    response = requests.get(
        f"{api_url}/api/devices",
        headers=service_headers
    )
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Test that the token does not have write access to devices
    test_device_data = {
        "hostname": f"test-device-{uuid.uuid4().hex[:8]}",
        "ip_address": "192.168.1.100",
        "device_type": "cisco_ios",
        "username": "test",
        "password": "test"
    }
    
    response = requests.post(
        f"{api_url}/api/devices",
        headers=service_headers,
        json=test_device_data
    )
    
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"


def test_service_token_with_limited_scopes(app_config, admin_token):
    """Test service token with limited scopes."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Create a service token with a single specific scope
    service_name = f"limited-scope-service-{uuid.uuid4().hex[:8]}"
    service_token_data = {
        "service_name": service_name,
        "scopes": ["read:devices"],  # Only read:devices scope
        "expiration_days": 7
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=service_token_data
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Get the service token
    service_token = response.json()["access_token"]
    service_headers = create_auth_headers(service_token)
    
    # Test that the token can access devices (read:devices scope)
    response = requests.get(
        f"{api_url}/api/devices",
        headers=service_headers
    )
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Test that the token cannot access backups (no read:backups scope)
    response = requests.get(
        f"{api_url}/api/backups",
        headers=service_headers
    )
    
    assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"


def test_token_listing(app_config, admin_token):
    """Test token listing endpoint."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Create a service token to list
    service_name = f"list-test-service-{uuid.uuid4().hex[:8]}"
    service_token_data = {
        "service_name": service_name,
        "scopes": ["read:devices"],
        "expiration_days": 1
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=service_token_data
    )
    
    assert response.status_code == 200, f"Failed to create service token: {response.status_code} - {response.text}"
    
    # List all tokens
    response = requests.get(
        f"{api_url}/api/auth/tokens",
        headers=headers
    )
    
    # Verify response status code
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Verify response data structure
    tokens = response.json()
    assert isinstance(tokens, list), "Expected a list of tokens"
    
    # Verify at least our admin token and the service token are included
    assert len(tokens) >= 2, f"Expected at least 2 tokens, got {len(tokens)}"
    
    # Check token fields
    if tokens:
        token = tokens[0]
        assert "id" in token, "Token missing 'id' field"
        assert "subject" in token, "Token missing 'subject' field"
        assert "issued_at" in token, "Token missing 'issued_at' field"
        assert "expires_at" in token, "Token missing 'expires_at' field"
        assert "scopes" in token, "Token missing 'scopes' field"
        
        # Check if our service token is in the list
        found_service_token = False
        for t in tokens:
            if t.get("subject") == service_name:
                found_service_token = True
                break
        
        assert found_service_token, f"Service token {service_name} not found in token list"


def test_token_revocation_single(app_config, admin_token):
    """Test single token revocation endpoint."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Create a service token to revoke
    service_name = f"revoke-test-service-{uuid.uuid4().hex[:8]}"
    service_token_data = {
        "service_name": service_name,
        "scopes": ["read:devices"],
        "expiration_days": 1
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=service_token_data
    )
    
    assert response.status_code == 200, f"Failed to create service token: {response.status_code} - {response.text}"
    service_token = response.json()["access_token"]
    
    # List tokens to get the token ID
    response = requests.get(
        f"{api_url}/api/auth/tokens",
        headers=headers
    )
    
    assert response.status_code == 200, f"Failed to list tokens: {response.status_code} - {response.text}"
    tokens = response.json()
    
    # Find the token ID for our service token
    token_id = None
    for token in tokens:
        if token.get("subject") == service_name:
            token_id = token.get("id")
            break
    
    assert token_id is not None, f"Could not find token ID for service {service_name}"
    
    # Revoke the token
    response = requests.delete(
        f"{api_url}/api/auth/tokens/{token_id}",
        headers=headers
    )
    
    # Verify response status code
    assert response.status_code == 204, f"Expected 204 No Content, got {response.status_code}: {response.text}"
    
    # Verify the token no longer works
    service_headers = create_auth_headers(service_token)
    response = requests.get(
        f"{api_url}/api/devices",
        headers=service_headers
    )
    
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"


def test_token_revocation_bulk(app_config, admin_token):
    """Test bulk token revocation endpoint."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Create multiple service tokens
    tokens = []
    for i in range(3):
        service_name = f"bulk-revoke-test-{i}-{uuid.uuid4().hex[:6]}"
        service_token_data = {
            "service_name": service_name,
            "scopes": ["read:devices"],
            "expiration_days": 1
        }
        
        response = requests.post(
            f"{api_url}/api/auth/service-token",
            headers=headers,
            json=service_token_data
        )
        
        assert response.status_code == 200, f"Failed to create service token: {response.status_code} - {response.text}"
        tokens.append(response.json()["access_token"])
    
    # Revoke all tokens (except admin token)
    response = requests.delete(
        f"{api_url}/api/auth/tokens",
        headers=headers,
        params={"exclude_current": "true"}  # Don't revoke the admin token we're using
    )
    
    # Verify response status code
    assert response.status_code == 204, f"Expected 204 No Content, got {response.status_code}: {response.text}"
    
    # Verify the service tokens no longer work
    for token in tokens:
        service_headers = create_auth_headers(token)
        response = requests.get(
            f"{api_url}/api/devices",
            headers=service_headers
        )
        
        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"
    
    # Verify our admin token still works
    response = requests.get(
        f"{api_url}/api/devices",
        headers=headers
    )
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"


def test_token_security_features(app_config, admin_token):
    """Test token security features."""
    headers = create_auth_headers(admin_token)
    api_url = app_config['api_url']
    
    # Test 1: Token with invalid format
    invalid_token_headers = {"Authorization": "Bearer invalid-token-format"}
    response = requests.get(
        f"{api_url}/api/devices",
        headers=invalid_token_headers
    )
    
    assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"
    
    # Test 2: Created token with very short expiration
    service_name = f"short-lived-token-{uuid.uuid4().hex[:8]}"
    service_token_data = {
        "service_name": service_name,
        "scopes": ["read:devices"],
        "expiration_hours": 1  # Very short-lived token (1 hour)
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=service_token_data
    )
    
    assert response.status_code == 200, f"Failed to create service token: {response.status_code} - {response.text}"
    
    # Verify token includes expires_in field with short duration
    token_response = response.json()
    assert "expires_in" in token_response, "Response missing 'expires_in' field"
    assert token_response["expires_in"] <= 3600, f"Expected expires_in <= 3600, got {token_response['expires_in']}"
    
    # Test 3: Attempt to create a token with excessive scopes
    excessive_scopes_data = {
        "service_name": f"excessive-scopes-{uuid.uuid4().hex[:8]}",
        "scopes": ["admin:*", "read:*", "write:*"],  # Try to get admin privileges
        "expiration_days": 30
    }
    
    response = requests.post(
        f"{api_url}/api/auth/service-token",
        headers=headers,
        json=excessive_scopes_data
    )
    
    # This should either be rejected (403) or sanitized (200 with reduced scopes)
    if response.status_code == 200:
        # If allowed, check that admin:* scope is not included
        token_data = response.json()
        service_token = token_data["access_token"]
        service_headers = create_auth_headers(service_token)
        
        # Try to access an admin-only endpoint
        response = requests.get(
            f"{api_url}/api/users",  # Typically admin-only
            headers=service_headers
        )
        
        assert response.status_code == 403, f"Expected 403 Forbidden, got {response.status_code}: {response.text}"
    elif response.status_code in [400, 403]:
        # If rejected entirely, that's also acceptable
        pass
    else:
        assert False, f"Unexpected status code: {response.status_code}: {response.text}"


def test_token_refresh_flow(app_config, api_token):
    """Test token refresh flow using refresh token."""
    # First, get the current user profile to verify the token works
    headers = create_auth_headers(api_token)
    user_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    assert user_response.status_code == 200, f"Initial token validation failed: {user_response.status_code}"
    original_user = user_response.json()
    
    # Now try to refresh the token
    # Note: This assumes the API returns a refresh token along with the access token
    # If the refresh endpoint doesn't exist or requires different parameters,
    # this test will need to be adjusted
    refresh_response = requests.post(
        f"{app_config['api_url']}/api/auth/refresh",
        headers=headers
    )
    
    # If the refresh endpoint exists and returns a new token
    if refresh_response.status_code == 200:
        data = refresh_response.json()
        assert "access_token" in data, "Response missing 'access_token' field"
        
        # Verify token format (typically JWT tokens start with "ey")
        assert data["access_token"].startswith("ey") or len(data["access_token"]) > 20, "Token format appears invalid"
        
        # Optionally verify the new token works
        new_headers = create_auth_headers(data["access_token"])
        new_user_response = requests.get(
            f"{app_config['api_url']}/api/users/me",
            headers=new_headers
        )
        assert new_user_response.status_code == 200, f"New token failed authentication: {new_user_response.status_code}"
        
        # Verify it's the same user
        new_user = new_user_response.json()
        assert new_user["username"] == original_user["username"], "Username mismatch after token refresh"
    else:
        # The refresh endpoint might not be implemented yet
        pytest.skip(f"Token refresh endpoint returned {refresh_response.status_code}: {refresh_response.text}")


def test_token_scope_verification(app_config, api_token):
    """Test that token scopes are properly enforced."""
    headers = create_auth_headers(api_token)
    
    # Test access to different endpoints with varying permission requirements
    # First verify the token works for a basic endpoint
    status_response = requests.get(
        f"{app_config['api_url']}/api/gateway/status",
        headers=headers
    )
    assert status_response.status_code == 200, f"Token not working for basic endpoint: {status_response.status_code}"
    
    # Test endpoints with different permission requirements
    endpoints = [
        # Format: (endpoint, method, expected_status)
        # The admin token should have access to all these endpoints
        ("/api/users", "GET", 200),  # Admin function - should be accessible
        ("/api/devices", "GET", 200),  # Basic devices endpoint - should be accessible
        ("/api/gateway/config", "GET", 200)  # Gateway config - should be accessible
    ]
    
    # Test each endpoint
    for endpoint, method, expected_status in endpoints:
        if method == "GET":
            response = requests.get(
                f"{app_config['api_url']}{endpoint}",
                headers=headers
            )
        else:
            response = requests.post(
                f"{app_config['api_url']}{endpoint}",
                headers=headers,
                json={}
            )
        
        # Skip if the endpoint doesn't exist
        if response.status_code == 404:
            continue
            
        # Verify the admin token has access
        assert response.status_code == expected_status, f"Expected {expected_status} for {endpoint}, got: {response.status_code}"


def test_login_with_valid_credentials(app_config):
    """Test login process with valid credentials."""
    # Use the known admin credentials
    login_data = {
        "username": "admin",
        "password": "NetRaven"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json=login_data
    )
    
    # Verify successful login
    assert response.status_code == 200, f"Login failed: {response.status_code}: {response.text}"
    
    # Verify response contains token
    data = response.json()
    assert "access_token" in data, "Response missing 'access_token' field"
    
    # Verify token format
    token = data["access_token"]
    assert token.startswith("ey") or len(token) > 20, "Token format appears invalid"
    
    # Verify token works
    headers = create_auth_headers(token)
    user_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=headers
    )
    assert user_response.status_code == 200, f"Token validation failed: {user_response.status_code}"
    
    # Verify correct user
    user_data = user_response.json()
    assert user_data["username"] == "admin", f"Expected admin user, got {user_data['username']}"


def test_login_with_invalid_credentials(app_config):
    """Test login process with invalid credentials."""
    # Use invalid credentials
    login_data = {
        "username": "admin",
        "password": "wrong-password"
    }
    
    response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json=login_data
    )
    
    # Verify authentication fails with 401
    assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"


def test_auth_event_logging(app_config, api_token):
    """Test authentication event logging."""
    headers = create_auth_headers(api_token)
    
    # 1. Generate a login event
    login_data = {
        "username": "admin",
        "password": "NetRaven"
    }
    
    login_response = requests.post(
        f"{app_config['api_url']}/api/auth/token",
        json=login_data
    )
    assert login_response.status_code == 200, "Login failed, cannot test auth events"
    
    # 2. Check if we can access the auth events log (admin access required)
    log_response = requests.get(
        f"{app_config['api_url']}/api/auth/events",
        headers=headers
    )
    
    # If the auth events endpoint exists
    if log_response.status_code == 200:
        log_data = log_response.json()
        assert isinstance(log_data, list), "Expected a list of auth events"
        
        # If logs exist, check their structure
        if len(log_data) > 0:
            event = log_data[0]
            assert "timestamp" in event, "Event missing 'timestamp' field"
            assert "event_type" in event, "Event missing 'event_type' field"
            assert "user_id" in event or "username" in event, "Event missing user identifier"
            
            # Look for metadata in the event (optional field)
            if "metadata" in event:
                assert isinstance(event["metadata"], dict), "Event metadata should be a dictionary"
    else:
        # The auth events endpoint might not be implemented yet
        pytest.skip(f"Auth events endpoint returned {log_response.status_code}: {log_response.text}")


def test_session_management_logout(app_config, api_token):
    """Test session management with logout."""
    headers = create_auth_headers(api_token)
    
    # First verify the token works
    status_response = requests.get(
        f"{app_config['api_url']}/api/gateway/status",
        headers=headers
    )
    assert status_response.status_code == 200, "Token not working before logout test"
    
    # Now logout
    logout_response = requests.post(
        f"{app_config['api_url']}/api/auth/logout",
        headers=headers
    )
    
    # If the logout endpoint exists
    if logout_response.status_code in [200, 204]:
        # Verify the token no longer works (should be invalidated)
        after_logout_response = requests.get(
            f"{app_config['api_url']}/api/gateway/status",
            headers=headers
        )
        
        # After logout, the token should be invalid
        assert after_logout_response.status_code in [401, 403], f"Token still valid after logout: {after_logout_response.status_code}"
    else:
        # The logout endpoint might not be implemented yet
        pytest.skip(f"Logout endpoint returned {logout_response.status_code}: {logout_response.text}")


def test_token_validation(app_config, api_token):
    """Test token validation for various scenarios."""
    # Test with valid token
    valid_headers = create_auth_headers(api_token)
    valid_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=valid_headers
    )
    assert valid_response.status_code == 200, "Valid token rejected"
    
    # Test with invalid token
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnZhbGlkIiwiaWF0IjoxNTE2MjM5MDIyfQ.invalid-signature"
    invalid_headers = create_auth_headers(invalid_token)
    invalid_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=invalid_headers
    )
    assert invalid_response.status_code in [401, 403], f"Invalid token accepted: {invalid_response.status_code}"
    
    # Test with missing token
    missing_token_response = requests.get(
        f"{app_config['api_url']}/api/users/me"
    )
    assert missing_token_response.status_code in [401, 403], f"Missing token accepted: {missing_token_response.status_code}"
    
    # Test with malformed token
    malformed_headers = {"Authorization": "Bearer not-a-token"}
    malformed_response = requests.get(
        f"{app_config['api_url']}/api/users/me",
        headers=malformed_headers
    )
    assert malformed_response.status_code in [401, 403], f"Malformed token accepted: {malformed_response.status_code}"

# --- New Token Lifecycle Tests ---

@pytest.fixture(scope="module")
def user_credentials() -> Dict[str, str]:
    """Provides standard user credentials for testing."""
    # Ensure these credentials match a user seeded in your test DB
    return {"username": "testuser", "password": "testpassword"}

@pytest.fixture(scope="module")
async def get_tokens(async_client: AsyncClient, user_credentials: Dict[str, str]) -> Tuple[str, str]:
    """Fixture to log in and get initial access and refresh tokens."""
    login_data = {
        "username": user_credentials["username"],
        "password": user_credentials["password"],
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    response.raise_for_status() # Ensure login was successful
    token_data = response.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    return token_data["access_token"], token_data["refresh_token"]

@pytest.mark.asyncio
async def test_successful_login_and_token_issuance(async_client: AsyncClient, user_credentials: Dict[str, str]):
    """Test successful login returns valid access and refresh tokens."""
    login_data = {
        "username": user_credentials["username"],
        "password": user_credentials["password"],
    }
    response = await async_client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    token_data = response.json()
    
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert "expires_in" in token_data
    assert "refresh_expires_in" in token_data
    assert "jti" in token_data
    
    # Optionally decode and check claims (adjust secret as needed)
    try:
        access_payload = jwt.decode(
            token_data["access_token"], 
            settings.TOKEN_SECRET_KEY, 
            algorithms=[settings.TOKEN_ALGORITHM],
            options={"verify_aud": False} # Adjust if audience is used
        )
        assert access_payload["sub"] == user_credentials["username"]
        assert "scope" in access_payload
        assert access_payload.get("token_type") == "access"

        refresh_payload = jwt.decode(
            token_data["refresh_token"], 
            settings.TOKEN_SECRET_KEY, 
            algorithms=[settings.TOKEN_ALGORITHM],
            options={"verify_aud": False}
        )
        assert refresh_payload["sub"] == user_credentials["username"]
        assert refresh_payload.get("token_type") == "refresh"
        
    except jwt.PyJWTError as e:
        pytest.fail(f"Token decoding failed: {e}")

@pytest.mark.asyncio
async def test_access_protected_endpoint_with_valid_token(async_client: AsyncClient, get_tokens: Tuple[str, str]):
    """Test accessing a protected endpoint with a valid token."""
    access_token, _ = get_tokens
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Use /users/me as a sample protected endpoint
    response = await async_client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == 200
    user_info = response.json()
    assert "username" in user_info
    assert user_info["username"] # Check it matches logged in user if possible

@pytest.mark.asyncio
async def test_access_protected_endpoint_without_token(async_client: AsyncClient):
    """Test accessing protected endpoint without any token fails."""
    response = await async_client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers # Middleware should add this

@pytest.mark.asyncio
async def test_access_protected_endpoint_with_invalid_token(async_client: AsyncClient):
    """Test accessing protected endpoint with an invalid/malformed token fails."""
    headers = {"Authorization": "Bearer invalid-token-string"}
    response = await async_client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    error_detail = response.json().get("detail")
    assert "Invalid token" in error_detail or "Not authenticated" in error_detail

@pytest.mark.asyncio
async def test_access_protected_endpoint_with_expired_token(async_client: AsyncClient, user_credentials: Dict[str, str]):
    """Test accessing protected endpoint with an expired token fails."""
    # Create a token with a very short expiry (e.g., -1 second)
    expired_payload = {
        "sub": user_credentials["username"],
        "exp": datetime.utcnow() - timedelta(seconds=1),
        "iat": datetime.utcnow() - timedelta(minutes=1),
        "token_type": "access",
        "scope": "read:*", # Add necessary scopes
        "jti": str(uuid.uuid4())
    }
    expired_token = jwt.encode(expired_payload, settings.TOKEN_SECRET_KEY, algorithm=settings.TOKEN_ALGORITHM)
    
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await async_client.get("/api/v1/users/me", headers=headers)
    
    assert response.status_code == 401
    assert "WWW-Authenticate" in response.headers
    error_detail = response.json().get("detail")
    assert "Token has expired" in error_detail

@pytest.mark.asyncio
async def test_successful_token_refresh(async_client: AsyncClient, get_tokens: Tuple[str, str]):
    """Test successfully refreshing an access token using a refresh token."""
    _, refresh_token = get_tokens
    
    refresh_data = {"refresh_token": refresh_token}
    # Allow some time if expiry is very short
    # time.sleep(1)
    response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
    
    assert response.status_code == 200
    new_token_data = response.json()
    
    assert "access_token" in new_token_data
    assert "refresh_token" in new_token_data # Check if rotation is enabled
    assert new_token_data["token_type"] == "bearer"
    
    # Verify the new access token works
    new_access_token = new_token_data["access_token"]
    headers = {"Authorization": f"Bearer {new_access_token}"}
    me_response = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200

@pytest.mark.asyncio
async def test_refresh_with_invalid_refresh_token(async_client: AsyncClient):
    """Test refreshing with an invalid/malformed refresh token fails."""
    refresh_data = {"refresh_token": "invalid-refresh-token"}
    response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 401 # Expecting unauthorized
    error_detail = response.json().get("detail")
    assert "Invalid token" in error_detail or "Invalid refresh token" in error_detail

@pytest.mark.asyncio
async def test_refresh_with_expired_refresh_token(async_client: AsyncClient, user_credentials: Dict[str, str]):
    """Test refreshing with an expired refresh token fails."""
     # Create an expired refresh token
    expired_payload = {
        "sub": user_credentials["username"],
        "exp": datetime.utcnow() - timedelta(seconds=1),
        "iat": datetime.utcnow() - timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES + 1),
        "token_type": "refresh",
        "jti": str(uuid.uuid4())
    }
    expired_refresh_token = jwt.encode(expired_payload, settings.TOKEN_SECRET_KEY, algorithm=settings.TOKEN_ALGORITHM)

    refresh_data = {"refresh_token": expired_refresh_token}
    response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
    assert response.status_code == 401
    error_detail = response.json().get("detail")
    assert "Token has expired" in error_detail or "Refresh token expired" in error_detail

@pytest.mark.asyncio
async def test_refresh_with_revoked_access_token_after_refresh(async_client: AsyncClient, get_tokens: Tuple[str, str]):
    """Test that the original access token is invalid after a refresh."""
    access_token, refresh_token = get_tokens
    
    # Refresh the token
    refresh_data = {"refresh_token": refresh_token}
    refresh_response = await async_client.post("/api/v1/auth/refresh", json=refresh_data)
    assert refresh_response.status_code == 200
    
    # Try using the *original* access token again
    original_headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await async_client.get("/api/v1/users/me", headers=original_headers)
    
    # Assuming token revocation/store check happens
    assert me_response.status_code == 401 
    error_detail = me_response.json().get("detail")
    # Detail might vary based on implementation (Invalid token, Token not found, etc.)
    assert "Invalid token" in error_detail or "Token not found" in error_detail

@pytest.mark.asyncio
async def test_logout_revokes_token(async_client: AsyncClient, get_tokens: Tuple[str, str]):
    """Test that the /logout endpoint revokes the current access token."""
    access_token, _ = get_tokens
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Logout
    logout_response = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    
    # Try using the token again
    me_response = await async_client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 401
    error_detail = me_response.json().get("detail")
    assert "Invalid token" in error_detail or "Token not found" in error_detail or "Token has been revoked" in error_detail

# Add more tests as needed, e.g., for logout-all, specific scope interactions, cookie handling 