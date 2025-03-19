"""
Tests for token refresh functionality.
"""
import pytest
import time
from playwright.sync_api import expect

from tests.ui.pages.auth_page import AuthPage


@pytest.fixture
def auth_page(authenticated_page, app_config):
    """Return an AuthPage instance with an authenticated page."""
    return AuthPage(authenticated_page, app_config)


def test_token_creation(auth_page):
    """Test creating a new token."""
    # Navigate to token management
    auth_page.navigate_to_token_management()
    
    # Create a new token
    token = auth_page.create_token("Test Token")
    
    # Verify token was created
    assert token is not None, "Token creation failed"
    assert len(token) > 20, "Token seems too short to be valid"
    
    # Verify token appears in list
    token_list = auth_page.get_tokens_list()
    assert len(token_list) > 0, "No tokens found in list"


def test_token_revocation(auth_page):
    """Test revoking a token."""
    # Navigate to token management
    auth_page.navigate_to_token_management()
    
    # Create a token to revoke
    auth_page.create_token("Token to Revoke")
    
    # Get all tokens
    tokens = auth_page.page.locator('.token-list-row').all()
    assert len(tokens) > 0, "No tokens available to revoke"
    
    # Find the token we just created (should be first in list)
    token_id = tokens[0].get_attribute('data-test-token-id')
    assert token_id is not None, "Could not find token ID"
    
    # Revoke the token
    success = auth_page.revoke_token(token_id)
    
    # Verify revocation was successful
    assert success, "Token revocation failed"


def test_session_persistence(auth_page):
    """Test that the session persists after page refresh."""
    # Record current URL
    current_url = auth_page.page.url
    
    # Refresh the page
    auth_page.page.reload()
    
    # Wait for page to load
    auth_page.page.wait_for_load_state("networkidle")
    
    # Check that we're still on the same page (not redirected to login)
    assert auth_page.page.url == current_url, "Session was lost after page refresh"
    
    # Verify a protected element is visible
    expect(auth_page.page.locator('[data-test="user-menu"]')).to_be_visible()


def test_logout_redirect(auth_page):
    """Test that logout redirects to the login page."""
    # Perform logout
    success = auth_page.logout()
    
    # Verify logout was successful
    assert success, "Logout failed"
    
    # Verify we're on login page
    assert "login" in auth_page.page.url.lower(), "Not redirected to login page after logout"
    
    # Verify login form is visible
    expect(auth_page.page.locator('form.login-form')).to_be_visible()


def test_user_profile_access(auth_page):
    """Test accessing user profile information."""
    # Get current user info
    user_info = auth_page.get_current_user_info()
    
    # Verify user info contains expected fields
    assert "username" in user_info, "Username not found in user info"
    assert "email" in user_info, "Email not found in user info"
    
    # Verify username is not empty
    assert user_info["username"], "Username is empty"


@pytest.mark.skip(reason="Requires token expiration configuration")
def test_token_expiration_and_refresh():
    """Test token expiration and refresh functionality.
    
    Note: This test is skipped by default as it requires specific token expiration configuration.
    To run this test, configure a short-lived token for testing.
    """
    # This would test that:
    # 1. A token expires after the configured time
    # 2. We can refresh the token before expiration
    # 3. After refresh, the old token is no longer valid
    # 4. The new token works correctly
    pass


def test_token_visible_after_creation(auth_page):
    """Test that the token is visible after creation for copying."""
    # Navigate to token management
    auth_page.navigate_to_token_management()
    
    # Create a new token
    token = auth_page.create_token("Visible Token Test")
    
    # Verify token is displayed in the UI for copying
    token_display = auth_page.page.locator('[data-test="new-token-value"]')
    expect(token_display).to_be_visible()
    
    # Verify displayed token matches the returned token
    assert token_display.text_content() == token, "Displayed token doesn't match returned token"


def test_token_not_visible_after_creation_confirmation(auth_page):
    """Test that the token is not visible after confirming creation."""
    # Navigate to token management
    auth_page.navigate_to_token_management()
    
    # Create a new token
    auth_page.create_token("Hidden Token Test")
    
    # Click the confirmation button to acknowledge token copy
    auth_page.page.click('[data-test="confirm-token-copy"]')
    
    # Verify token is no longer displayed
    token_display = auth_page.page.locator('[data-test="new-token-value"]')
    expect(token_display).to_have_count(0)


def test_active_token_indicator(auth_page):
    """Test that active tokens have a visual indicator."""
    # Navigate to token management
    auth_page.navigate_to_token_management()
    
    # Create a token to ensure we have at least one active token
    auth_page.create_token("Active Token Test")
    auth_page.page.click('[data-test="confirm-token-copy"]')
    
    # Verify that at least one token has an active indicator
    active_indicators = auth_page.page.locator('[data-test="active-token-indicator"]').all()
    assert len(active_indicators) > 0, "No active token indicators found" 