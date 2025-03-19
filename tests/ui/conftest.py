"""
Pytest fixtures for UI testing with Playwright.
"""
import pytest
import os
import time
import logging
from playwright.sync_api import expect, Page

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for testing
DEFAULT_TIMEOUT = 10000  # 10 seconds
DEFAULT_BASE_URL = "http://frontend:8080"

@pytest.fixture(scope="session")
def app_config():
    """Return the application configuration."""
    return {
        "ui_url": os.environ.get("UI_TEST_URL", DEFAULT_BASE_URL),
        "api_url": os.environ.get("API_TEST_URL", "http://api:8000"),
        "admin_user": os.environ.get("ADMIN_TEST_USER", "admin"),
        "admin_password": os.environ.get("ADMIN_TEST_PASSWORD", "NetRaven"),
        "test_timeout": int(os.environ.get("TEST_TIMEOUT", DEFAULT_TIMEOUT))
    }

@pytest.fixture
def page_config(page: Page, app_config):
    """Configure the page with default settings."""
    # Set default timeout
    page.set_default_timeout(app_config["test_timeout"])
    
    # Add helpers to the page
    page.wait_for_network_idle = lambda timeout=5000: page.wait_for_load_state("networkidle", timeout=timeout)
    
    return page

@pytest.fixture
def authenticated_page(page_config, app_config):
    """Return a page object that's already logged in."""
    page = page_config
    
    try:
        # Navigate to login page
        page.goto(app_config["ui_url"])
        
        # Check if already on dashboard (may happen if session persists)
        if page.url.endswith("/dashboard"):
            return page
        
        # Login with admin credentials
        page.fill('input[name="username"]', app_config["admin_user"])
        page.fill('input[name="password"]', app_config["admin_password"])
        page.click('button[type="submit"]')
        
        # Wait for dashboard to load
        page.wait_for_selector('.dashboard', timeout=app_config["test_timeout"])
        
        # Wait for any network activity to subside
        page.wait_for_network_idle()
        
        return page
    except Exception as e:
        # Take screenshot on failure for debugging
        if not os.path.exists("test-artifacts"):
            os.makedirs("test-artifacts")
        timestamp = int(time.time())
        page.screenshot(path=f"test-artifacts/auth_failure_{timestamp}.png")
        raise e

@pytest.fixture(autouse=True)
def cleanup_test_resources(page, authenticated_page, request):
    """Clean up any test resources after each test."""
    # Run the test first
    yield
    
    # Skip cleanup for tests that are marked as no_cleanup
    if request.node.get_closest_marker("no_cleanup"):
        logger.info("Skipping cleanup for test marked with no_cleanup")
        return
    
    # After test, clean up all test data with prefix "test-"
    try:
        logger.info("Running cleanup for test resources")
        
        # First navigate to dashboard to ensure we're in a neutral state
        authenticated_page.goto(f"{authenticated_page.url.split('#')[0]}#/dashboard")
        
        # Clean up users
        try:
            authenticated_page.goto(f"{authenticated_page.url.split('#')[0]}#/users")
            # Wait for users to load
            authenticated_page.wait_for_selector('.users-list', timeout=5000)
            
            # Find all test user rows
            test_users = authenticated_page.locator("[data-test^='user-row-test-']").all()
            
            for user_element in test_users:
                try:
                    # Extract username from data-test attribute
                    data_test = user_element.get_attribute('data-test')
                    username = data_test.replace('user-row-', '')
                    
                    # Click delete button for this user
                    authenticated_page.click(f"[data-test='delete-user-{username}']")
                    authenticated_page.click("[data-test='confirm-delete-button']")
                    authenticated_page.wait_for_network_idle()
                    logger.info(f"Cleaned up test user: {username}")
                except Exception as e:
                    logger.warning(f"Error cleaning up user: {str(e)}")
        except Exception as e:
            logger.warning(f"Error during user cleanup: {str(e)}")
            
        # Add similar cleanup blocks for other resource types like devices, tokens, etc.
        # as they are implemented in tests
            
    except Exception as e:
        logger.error(f"Error in cleanup: {str(e)}")
        # Don't fail the test if cleanup fails
        pass 