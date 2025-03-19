"""
Tests for the login functionality.
"""
import pytest
from playwright.sync_api import expect
from tests.ui.pages.login_page import LoginPage


def test_valid_login(page, app_config):
    """Test login with valid credentials."""
    login_page = LoginPage(page, app_config["ui_url"])
    login_page.navigate().login(
        app_config["admin_user"], 
        app_config["admin_password"]
    )
    
    # Verify redirect to dashboard
    login_page.wait_for_successful_login()
    login_page.expect_to_be_visible('.dashboard')


def test_invalid_login(page, app_config):
    """Test login with invalid credentials."""
    login_page = LoginPage(page, app_config["ui_url"])
    login_page.navigate().login(
        app_config["admin_user"], 
        "wrong-password"
    )
    
    # Verify error message and no redirect
    assert login_page.has_error_message()


def test_empty_credentials(page, app_config):
    """Test login with empty credentials."""
    login_page = LoginPage(page, app_config["ui_url"])
    login_page.navigate().login("", "")
    
    # Verify form validation error
    login_page.expect_to_be_visible('text=Username is required')


def test_login_navigation(page, app_config):
    """Test navigation to login page."""
    login_page = LoginPage(page, app_config["ui_url"])
    login_page.navigate()
    
    # Verify login elements are present
    login_page.expect_to_be_visible('input[name="username"]')
    login_page.expect_to_be_visible('input[name="password"]')
    login_page.expect_to_be_visible('button[type="submit"]')


def test_token_persistence(page, app_config):
    """Test that the authentication token persists after navigation."""
    # First, log in
    login_page = LoginPage(page, app_config["ui_url"])
    login_page.navigate().login(
        app_config["admin_user"], 
        app_config["admin_password"]
    )
    login_page.wait_for_successful_login()
    
    # Navigate away and back
    page.goto(f"{app_config['ui_url']}/devices")
    page.goto(f"{app_config['ui_url']}/dashboard")
    
    # Verify we're still logged in
    login_page.expect_to_be_visible('.dashboard')
    
    # Verify username is displayed in the header
    login_page.expect_to_be_visible(f'text={app_config["admin_user"]}') 