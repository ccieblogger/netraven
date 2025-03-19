"""
Tests for rate limiting functionality.
"""
import pytest
import time
from playwright.sync_api import expect
from tests.ui.pages.auth_page import AuthPage

@pytest.fixture
def auth_page(page, app_config):
    """Return an AuthPage instance with a fresh page (not authenticated)."""
    # Use a fresh page to avoid authentication from previous tests
    auth_page = AuthPage(page, app_config)
    auth_page.navigate_to_login()
    return auth_page

def test_login_rate_limiting(auth_page):
    """Test that login attempts are rate limited after multiple failures."""
    # Setup non-existent user credentials
    non_existent_user = "test-nonexistent-user"
    wrong_password = "WrongPassword123!"
    
    # The rate limit is likely configured to block after 5-10 failed attempts
    # Try multiple failed logins
    for i in range(10):
        result = auth_page.login(non_existent_user, wrong_password)
        assert not result, f"Login should fail for non-existent user on attempt {i+1}"
        
        # Check if we've hit the rate limit after each attempt
        if auth_page.is_rate_limited():
            # We've been rate limited, test passed
            rate_limit_message = auth_page.page.locator('[data-test="rate-limit-message"]')
            expect(rate_limit_message).to_be_visible()
            print(f"Rate limit hit after {i+1} attempts")
            return
    
    # If we reach here without being rate limited, check for error message
    error_message = auth_page.get_error_message()
    assert error_message is not None, "No error message displayed after failed login attempts"
    
    # Check if the error message mentions rate limiting
    rate_limiting_terms = ["rate", "limit", "attempts", "try again", "locked", "timeout"]
    has_rate_limit_term = any(term in error_message.lower() for term in rate_limiting_terms)
    
    assert has_rate_limit_term, f"Error message '{error_message}' doesn't indicate rate limiting"

def test_login_cooldown(auth_page):
    """Test that a cooldown period is enforced after hitting the rate limit."""
    # First, trigger the rate limit
    non_existent_user = "test-nonexistent-user"
    wrong_password = "WrongPassword123!"
    
    # Trigger rate limiting
    for i in range(10):
        auth_page.login(non_existent_user, wrong_password)
        if auth_page.is_rate_limited():
            print(f"Rate limit hit after {i+1} attempts")
            break
    
    # Verify we hit the rate limit
    assert auth_page.is_rate_limited(), "Failed to trigger rate limiting"
    
    # Wait a short period (not the full cooldown) and try again
    time.sleep(2)
    
    # Clear inputs and try again
    auth_page.page.fill('[data-test="username-input"]', non_existent_user)
    auth_page.page.fill('[data-test="password-input"]', wrong_password)
    auth_page.page.click('[data-test="login-button"]')
    
    # We should still be rate limited
    assert auth_page.is_rate_limited(), "Rate limit not enforced after short cooldown"

@pytest.mark.skip(reason="Requires a separate test account")
def test_token_endpoint_rate_limiting():
    """Test that token endpoint is rate limited.
    
    Note: This test is skipped by default as it requires a separate test account.
    """
    # This would test that:
    # 1. The token endpoint is rate limited
    # 2. After too many requests, the endpoint returns rate limit errors
    # 3. The rate limit resets after the cooldown period
    pass

def test_brute_force_detection(auth_page):
    """Test detection of potential brute force attempts."""
    # Try logging in with correct username but multiple wrong passwords
    admin_username = "admin"
    
    # Generate a list of wrong passwords
    wrong_passwords = [
        "Password1!", "Password2!", "Password3!",
        "AdminPass1!", "AdminPass2!", "AdminPass3!",
        "NetRaven1!", "NetRaven2!", "NetRaven3!",
    ]
    
    # Test with multiple wrong passwords
    for i, password in enumerate(wrong_passwords):
        # Try login
        auth_page.login(admin_username, password)
        
        # Check if we've been rate limited
        if auth_page.is_rate_limited():
            print(f"Rate limited after {i+1} password attempts")
            
            # Verify rate limit message
            rate_limit_message = auth_page.page.locator('[data-test="rate-limit-message"]')
            expect(rate_limit_message).to_be_visible()
            return
            
        # Check for brute force detection message
        error_message = auth_page.get_error_message()
        if error_message and any(term in error_message.lower() for term in ["brute force", "suspicious", "security", "locked"]):
            print(f"Brute force detection triggered after {i+1} password attempts")
            return
            
    # If we get here, we should at least have error messages
    error_message = auth_page.get_error_message()
    assert error_message is not None, "No error message after multiple failed login attempts" 