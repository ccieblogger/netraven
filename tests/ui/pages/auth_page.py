"""
Page object for authentication operations.
"""
from playwright.sync_api import Page, expect
import logging
from .base_page import BasePage

logger = logging.getLogger(__name__)

class AuthPage(BasePage):
    """Page object for authentication operations."""
    
    def __init__(self, page: Page, app_config: dict):
        """Initialize the auth page."""
        super().__init__(page, app_config)
        self.login_url = f"{self.app_config['ui_url']}/#/login"
        
    def navigate_to_login(self):
        """Navigate to the login page."""
        self.page.goto(self.login_url)
        self.page.wait_for_selector('form.login-form', timeout=self.app_config["test_timeout"])
        self.page.wait_for_network_idle()
        return self
        
    def login(self, username, password):
        """Login with the provided credentials."""
        # Navigate to login page if not already there
        if not self.page.url.endswith('/login'):
            self.navigate_to_login()
            
        # Fill the form
        self.page.fill('[data-test="username-input"]', username)
        self.page.fill('[data-test="password-input"]', password)
        
        # Submit the form
        self.page.click('[data-test="login-button"]')
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check if we're redirected to dashboard (success) or still on login page (failure)
        try:
            # Wait for dashboard to appear
            self.page.wait_for_selector('.dashboard', timeout=5000)
            logger.info(f"Login successful for user {username}")
            return True
        except Exception as e:
            logger.warning(f"Login failed for user {username}: {str(e)}")
            return False
            
    def logout(self):
        """Logout the current user."""
        # Click on the user menu
        self.page.click('[data-test="user-menu"]')
        
        # Click on the logout option
        self.page.click('[data-test="logout-option"]')
        
        # Wait for redirect to login page
        try:
            self.page.wait_for_selector('form.login-form', timeout=5000)
            logger.info("Logout successful")
            return True
        except Exception as e:
            logger.warning(f"Logout failed: {str(e)}")
            return False
            
    def navigate_to_token_management(self):
        """Navigate to the token management page."""
        # Click on the user menu
        self.page.click('[data-test="user-menu"]')
        
        # Click on the tokens option
        self.page.click('[data-test="tokens-option"]')
        
        # Wait for token management page to load
        self.page.wait_for_selector('.tokens-list', timeout=5000)
        self.page.wait_for_network_idle()
        return self
        
    def get_tokens_list(self):
        """Get all token rows from the list."""
        return self.page.locator('.token-list-row').all()
        
    def create_token(self, description="API Token"):
        """Create a new token with the provided description."""
        # Navigate to token page if not already there
        self.navigate_to_token_management()
            
        # Click the 'Create Token' button
        self.page.click('[data-test="create-token-button"]')
        
        # Fill the description
        self.page.fill('[data-test="token-description-input"]', description)
        
        # Submit the form
        self.page.click('[data-test="submit-token-button"]')
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check for success and get the token
        token_text = self.page.locator('[data-test="new-token-value"]')
        try:
            expect(token_text).to_be_visible(timeout=5000)
            token_value = token_text.text_content()
            logger.info(f"Token created successfully: {description}")
            return token_value
        except Exception as e:
            logger.error(f"Failed to create token: {str(e)}")
            return None
            
    def revoke_token(self, token_id):
        """Revoke a token by its ID."""
        # Navigate to token page if not already there
        self.navigate_to_token_management()
            
        # Click the revoke button for this token
        self.page.click(f"[data-test='revoke-token-{token_id}']")
        
        # Confirm revocation
        self.page.click("[data-test='confirm-revoke-button']")
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check for success message
        success_message = self.page.locator('.success-notification')
        try:
            expect(success_message).to_be_visible(timeout=5000)
            logger.info(f"Token {token_id} revoked successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token {token_id}: {str(e)}")
            return False
            
    def get_current_user_info(self):
        """Get information about the currently logged in user."""
        # Click on the user menu
        self.page.click('[data-test="user-menu"]')
        
        # Click on the profile option
        self.page.click('[data-test="profile-option"]')
        
        # Wait for the profile page to load
        self.page.wait_for_selector('.profile-form', timeout=5000)
        
        # Get user information
        return {
            'username': self.page.locator('[data-test="profile-username"]').text_content(),
            'email': self.page.locator('[data-test="profile-email"]').text_content()
        }
        
    def is_rate_limited(self):
        """Check if the current login attempt is rate limited."""
        rate_limit_message = self.page.locator('[data-test="rate-limit-message"]')
        return rate_limit_message.count() > 0
        
    def get_error_message(self):
        """Get the error message if present."""
        error = self.page.locator('.error-notification')
        if error.count() > 0:
            return error.first.text_content()
        return None 