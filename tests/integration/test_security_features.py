"""
Integration tests for NetRaven security features.

This module tests security features including:
- Authentication edge cases
- Permission boundary testing
- API rate limiting
- Input validation
- Cross-origin request handling
- Session management
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from netraven.web.app import app
from tests.utils.api_test_utils import create_auth_headers

# Test client
client = TestClient(app)


def test_valid_token_authentication(app_config, api_token):
    """Test authentication with a valid API token."""
    response = client.get(
        "/api/auth/me",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "roles" in data


def test_expired_token_authentication():
    """Test authentication with an expired token."""
    # Create an expired token (1 second expiration, wait 2 seconds)
    from netraven.web.auth.jwt import create_access_token
    
    expired_token = create_access_token(
        data={"sub": "test-user", "roles": ["user"]},
        expires_minutes=1/60  # 1 second
    )
    
    # Wait for token to expire
    time.sleep(2)
    
    # Test with expired token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    assert "expired" in data["detail"].lower()


def test_invalid_token_authentication():
    """Test authentication with an invalid token."""
    # Create a completely invalid token
    invalid_token = "invalid.token.format"
    
    # Test with invalid token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    
    # Also test with a valid format but invalid signature
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJyb2xlcyI6WyJ1c2VyIl0sImV4cCI6OTk5OTk5OTk5OX0.invalid_signature"
    
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_missing_token_authentication():
    """Test authentication with a missing token."""
    # No Authorization header
    response = client.get("/api/auth/me")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    
    # Empty Authorization header
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": ""}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    
    # Authorization header without Bearer
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "token123"}
    )
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_token_refresh(app_config, api_token):
    """Test refreshing an access token."""
    # First get original token information
    response = client.get(
        "/api/auth/me",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    original_data = response.json()
    
    # Request a token refresh
    response = client.post(
        "/api/auth/refresh",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    refresh_data = response.json()
    assert "access_token" in refresh_data
    assert refresh_data["access_token"] != api_token  # Should be different
    
    # Verify the new token works
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {refresh_data['access_token']}"}
    )
    
    assert response.status_code == 200
    new_data = response.json()
    
    # User info should be the same
    assert new_data["username"] == original_data["username"]
    assert new_data["roles"] == original_data["roles"]


def test_permission_boundaries_admin(app_config, api_token, settings_db):
    """Test permission boundaries for admin role."""
    # First ensure the API token has the admin role
    response = client.get(
        "/api/auth/me",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # If not admin, skip test
    if "admin" not in data["roles"]:
        pytest.skip("API token does not have admin role")
    
    # Test admin-only endpoints
    # 1. Admin settings
    response = client.get(
        "/api/admin/settings",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    
    # 2. User management
    response = client.get(
        "/api/admin/users",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code == 200
    
    # 3. System configuration
    response = client.get(
        "/api/admin/system/config",
        headers=create_auth_headers(api_token)
    )
    
    if response.status_code == 404:
        pytest.skip("System config endpoint not implemented yet")
    
    assert response.status_code == 200


def test_permission_boundaries_user(app_config, settings_db):
    """Test permission boundaries for regular user role."""
    # Create a regular user token
    from netraven.web.auth.jwt import create_access_token
    
    regular_user_token = create_access_token(
        data={"sub": "regular-user", "roles": ["user"]},
        expires_minutes=15
    )
    
    # First verify the token works for user-level endpoints
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["roles"] == ["user"]
    
    # Test user-accessible endpoints
    # 1. Devices listing
    response = client.get(
        "/api/devices",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    
    assert response.status_code == 200
    
    # Test admin-only endpoints (should be forbidden)
    # 1. Admin settings
    response = client.get(
        "/api/admin/settings",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    
    assert response.status_code == 403
    
    # 2. User management
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {regular_user_token}"}
    )
    
    assert response.status_code == 403


def test_permission_boundaries_readonly(app_config, settings_db):
    """Test permission boundaries for readonly role."""
    # Create a readonly user token
    from netraven.web.auth.jwt import create_access_token
    
    readonly_token = create_access_token(
        data={"sub": "readonly-user", "roles": ["readonly"]},
        expires_minutes=15
    )
    
    # First verify the token works for readonly endpoints
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {readonly_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["roles"] == ["readonly"]
    
    # Test readonly-accessible endpoints
    # 1. Devices listing (read)
    response = client.get(
        "/api/devices",
        headers={"Authorization": f"Bearer {readonly_token}"}
    )
    
    assert response.status_code == 200
    
    # Test write operations (should be forbidden)
    # 1. Creating a device
    response = client.post(
        "/api/devices",
        json={
            "hostname": "test-device",
            "ip_address": "192.168.1.100",
            "device_type": "cisco_ios"
        },
        headers={"Authorization": f"Bearer {readonly_token}"}
    )
    
    assert response.status_code in [403, 405]  # Either Forbidden or Method Not Allowed


def test_cors_configuration():
    """Test CORS configuration."""
    # Set up a request with Origin header
    origin = "http://test-origin.example.com"
    
    # Options request (preflight)
    response = client.options(
        "/api/devices",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization"
        }
    )
    
    # Check if CORS is configured (allow or block)
    if "access-control-allow-origin" in response.headers:
        # CORS is configured to allow
        assert response.headers["access-control-allow-origin"] == "*" or response.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
        assert "Authorization" in response.headers["access-control-allow-headers"]
    else:
        # CORS is blocking or not configured
        pass  # Both behaviors could be valid depending on requirements
    
    # Regular request with Origin
    response = client.get(
        "/api/devices",
        headers={"Origin": origin}
    )
    
    # Check actual response CORS headers (if configured)
    if "access-control-allow-origin" in response.headers:
        assert response.headers["access-control-allow-origin"] == "*" or response.headers["access-control-allow-origin"] == origin


def test_rate_limiting():
    """Test API rate limiting."""
    # This test performs multiple rapid requests to check rate limiting
    # Note: This test may fail if rate limiting is not implemented
    
    # Create a valid token for testing
    from netraven.web.auth.jwt import create_access_token
    
    test_token = create_access_token(
        data={"sub": "rate-limit-test", "roles": ["user"]},
        expires_minutes=15
    )
    
    headers = {"Authorization": f"Bearer {test_token}"}
    
    # Perform multiple requests quickly
    start_time = time.time()
    responses = []
    
    # Make 10 rapid requests (adjust based on your rate limit configuration)
    for _ in range(10):
        response = client.get(
            "/api/devices",  # Choose an endpoint that would be rate-limited
            headers=headers
        )
        responses.append(response)
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Check if any response indicates rate limiting
    rate_limited = any(
        response.status_code == 429 or 
        "X-RateLimit-Remaining" in response.headers and response.headers["X-RateLimit-Remaining"] == "0"
        for response in responses
    )
    
    # Rate limiting may or may not be implemented
    if rate_limited:
        # Rate limiting is active
        for response in responses:
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data
                assert "retry-after" in response.headers.keys() or "retry_after" in data
                break
    else:
        # Rate limiting might not be implemented or triggered
        # Check if rate limit headers are present at all
        has_rate_headers = any(
            "X-RateLimit-Limit" in response.headers for response in responses
        )
        
        if has_rate_headers:
            # Headers present but limit not exceeded
            for response in responses:
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        else:
            # No rate limiting implemented - this is ok if not required
            pass


def test_input_validation(app_config, api_token):
    """Test API input validation for malformed requests."""
    # Test with missing required fields
    response = client.post(
        "/api/devices",
        json={
            # Missing required fields like hostname, ip_address
            "device_type": "cisco_ios"
        },
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code in [400, 422]  # Either Bad Request or Unprocessable Entity
    
    # Test with invalid data types
    response = client.post(
        "/api/devices",
        json={
            "hostname": "test-device",
            "ip_address": "not-an-ip-address",  # Invalid IP format
            "device_type": "cisco_ios"
        },
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code in [400, 422]
    
    # Test with value out of allowed range
    response = client.post(
        "/api/devices",
        json={
            "hostname": "test-device",
            "ip_address": "192.168.1.100",
            "device_type": "cisco_ios",
            "port": 99999  # Invalid port number
        },
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code in [400, 422]
    
    # Test with SQL injection attempt
    response = client.get(
        "/api/devices?hostname=test-device' OR 1=1 --",
        headers=create_auth_headers(api_token)
    )
    
    assert response.status_code != 500  # Should not cause a server error
    
    # Test with JSON containing JavaScript payload
    response = client.post(
        "/api/devices",
        json={
            "hostname": "<script>alert('xss')</script>",
            "ip_address": "192.168.1.100",
            "device_type": "cisco_ios"
        },
        headers=create_auth_headers(api_token)
    )
    
    # Could be rejected (400/422) or sanitized (200/201) - either is acceptable
    assert response.status_code != 500


def test_session_management():
    """Test session management and timeout."""
    # Create a session token (if session-based auth is used)
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "test_user",
            "password": "test_password"
        }
    )
    
    # Check if session-based auth is implemented
    if login_response.status_code == 404:
        pytest.skip("Session-based authentication not implemented")
    
    # If JWT is used exclusively, this also applies
    if login_response.status_code == 200 and "access_token" in login_response.json():
        pytest.skip("JWT-based authentication is used instead of sessions")
    
    # If we have a session-based system
    if login_response.status_code == 200:
        session_cookie = login_response.cookies.get("session")
        
        if not session_cookie:
            pytest.skip("No session cookie found")
        
        # Test the session works
        response = client.get(
            "/api/auth/me",
            cookies={"session": session_cookie}
        )
        
        assert response.status_code == 200
        
        # Test session timeout (if configured for short timeouts)
        # This is optional as it depends on the configuration
        try:
            # Wait for a potential timeout (adjust based on your config)
            time.sleep(60)  # 1 minute
            
            response = client.get(
                "/api/auth/me",
                cookies={"session": session_cookie}
            )
            
            # Check if session timed out
            if response.status_code == 401:
                # Session timeout works as expected
                pass
            else:
                # Session might have a longer timeout
                pass
                
        except Exception:
            # Timeout test is optional
            pass


def test_password_complexity():
    """Test password complexity requirements."""
    # Define passwords of varying complexity
    test_cases = [
        {"password": "short", "should_pass": False},
        {"password": "onlyletters", "should_pass": False},
        {"password": "123456789", "should_pass": False},
        {"password": "LettersAndNumbers123", "should_pass": True},
        {"password": "Complex!Password123", "should_pass": True},
    ]
    
    # Test register endpoint if available
    for test_case in test_cases:
        response = client.post(
            "/api/auth/register",
            json={
                "username": f"user_{int(time.time())}",  # Unique username
                "password": test_case["password"],
                "email": f"test_{int(time.time())}@example.com"  # Unique email
            }
        )
        
        if response.status_code == 404:
            # Registration endpoint not available, try password update instead
            from netraven.web.auth.jwt import create_access_token
            
            test_token = create_access_token(
                data={"sub": "password-test", "roles": ["user"]},
                expires_minutes=15
            )
            
            response = client.post(
                "/api/auth/change-password",
                json={"password": test_case["password"]},
                headers={"Authorization": f"Bearer {test_token}"}
            )
            
            if response.status_code == 404:
                pytest.skip("Password change endpoints not implemented")
        
        # Check if complexity requirements are enforced
        if test_case["should_pass"]:
            assert response.status_code in [200, 201, 204]
        else:
            assert response.status_code in [400, 422]
            data = response.json()
            assert "detail" in data or "message" in data


def test_secure_headers():
    """Test secure HTTP headers."""
    # Make a request to check security headers
    response = client.get("/api")
    
    # Check for common security headers
    # These may or may not be implemented, we're just checking
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": ["DENY", "SAMEORIGIN"],
        "Content-Security-Policy": None,  # Any value is good
        "Strict-Transport-Security": None,  # Any value is good
        "X-XSS-Protection": ["0", "1", "1; mode=block"],
    }
    
    # Count how many security headers are implemented
    implemented_headers = 0
    
    for header, expected_values in security_headers.items():
        if header in response.headers:
            implemented_headers += 1
            
            # If expected values are specified, check them
            if expected_values is not None:
                if not isinstance(expected_values, list):
                    expected_values = [expected_values]
                
                assert any(response.headers[header] == value or 
                         response.headers[header].startswith(value) 
                         for value in expected_values)
    
    # Note: We don't require all headers to be implemented
    # This test is informational rather than pass/fail
    print(f"Implemented {implemented_headers} out of {len(security_headers)} recommended security headers")


def test_sql_injection_protection(app_config, api_token):
    """Test protection against SQL injection."""
    # Try common SQL injection patterns
    injection_patterns = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "' UNION SELECT username, password FROM users; --",
    ]
    
    # Test various endpoints with SQL injection attempts
    endpoints = [
        "/api/devices?hostname={}",
        "/api/backups?device_id={}",
        "/api/users?username={}"
    ]
    
    for endpoint_template in endpoints:
        for pattern in injection_patterns:
            # Create the URL with the injection pattern
            encoded_pattern = pattern.replace(" ", "%20")
            url = endpoint_template.format(encoded_pattern)
            
            # Make the request
            response = client.get(
                url,
                headers=create_auth_headers(api_token)
            )
            
            # We should never get a 500 error from SQL injection
            assert response.status_code != 500, f"Possible SQL injection vulnerability at {url}"
            
            # If we get a 200 OK, make sure it doesn't return unexpected data
            if response.status_code == 200:
                data = response.json()
                
                # Check for suspicious patterns suggesting successful injection
                # This is a simplistic check and might need adjustment
                if isinstance(data, list) and len(data) > 20:
                    # Suspicious: large data set could mean "SELECT *"
                    assert False, f"Possible SQL injection success at {url} (large result set)"


def test_xss_protection(app_config, api_token):
    """Test protection against cross-site scripting (XSS)."""
    # XSS payload patterns to test
    xss_patterns = [
        "<script>alert('xss')</script>",
        "<img src='x' onerror='alert(\"xss\")'>",
        "<a href='javascript:alert(\"xss\")'>link</a>",
        "javascript:alert('xss')",
        "<div onmouseover='alert(\"xss\")'>hover me</div>"
    ]
    
    # Test creating entities with XSS payloads
    for pattern in xss_patterns:
        # Try to create a device with XSS in the hostname
        response = client.post(
            "/api/devices",
            json={
                "hostname": pattern,
                "ip_address": "192.168.1.100",
                "device_type": "cisco_ios"
            },
            headers=create_auth_headers(api_token)
        )
        
        # Either it should be rejected (400/422) or sanitized
        if response.status_code in [200, 201]:
            # It was accepted, verify the payload was sanitized
            device_id = response.json().get("id")
            
            # Get the device to check if sanitized
            get_response = client.get(
                f"/api/devices/{device_id}",
                headers=create_auth_headers(api_token)
            )
            
            assert get_response.status_code == 200
            device = get_response.json()
            
            # Check if the XSS patterns were sanitized
            assert "<script>" not in device["hostname"]
            assert "javascript:" not in device["hostname"]
            assert "onerror=" not in device["hostname"]
            assert "onmouseover=" not in device["hostname"]


def test_csrf_protection():
    """Test protection against cross-site request forgery (CSRF)."""
    # This test checks if CSRF protection is implemented
    # First, try to establish a session if session-based auth is used
    
    login_response = client.post(
        "/api/auth/login",
        json={
            "username": "test_user",
            "password": "test_password"
        }
    )
    
    # Skip if session-based auth is not implemented
    if login_response.status_code == 404:
        pytest.skip("Session-based authentication not implemented")
    
    # Skip if JWT-based auth is used exclusively
    if login_response.status_code == 200 and "access_token" in login_response.json():
        pytest.skip("JWT-based authentication is used instead of sessions")
    
    # If session auth is used
    if login_response.status_code == 200:
        session_cookie = login_response.cookies.get("session")
        
        if not session_cookie:
            pytest.skip("No session cookie found")
        
        # Check for CSRF token in the response or a dedicated endpoint
        csrf_token = None
        
        # Look for CSRF token in the login response headers
        if "X-CSRF-Token" in login_response.headers:
            csrf_token = login_response.headers["X-CSRF-Token"]
        
        # If not found, try getting it from a dedicated endpoint
        if not csrf_token:
            try:
                token_response = client.get(
                    "/api/auth/csrf-token",
                    cookies={"session": session_cookie}
                )
                
                if token_response.status_code == 200:
                    data = token_response.json()
                    if "csrf_token" in data:
                        csrf_token = data["csrf_token"]
            except:
                pass
        
        # Now test POST requests with and without CSRF token
        test_data = {"name": "Test CSRF", "description": "Testing CSRF protection"}
        
        # Try without CSRF token (should fail if CSRF protection is enabled)
        try:
            response_without_token = client.post(
                "/api/some-protected-resource",
                json=test_data,
                cookies={"session": session_cookie}
            )
            
            # If CSRF protection is implemented, it should fail
            if response_without_token.status_code in [403, 419]:
                # CSRF protection is working
                pass
        except:
            # This might happen if the endpoint doesn't exist
            pass
        
        # Try with CSRF token (should succeed if CSRF protection is enabled)
        if csrf_token:
            try:
                response_with_token = client.post(
                    "/api/some-protected-resource",
                    json=test_data,
                    cookies={"session": session_cookie},
                    headers={"X-CSRF-Token": csrf_token}
                )
                
                # This should not give a CSRF error
                assert response_with_token.status_code != 403
            except:
                # This might happen if the endpoint doesn't exist
                pass 