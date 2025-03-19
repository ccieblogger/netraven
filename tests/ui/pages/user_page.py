"""
Page object for user management operations.
"""
from playwright.sync_api import Page, expect
import logging
from .base_page import BasePage

logger = logging.getLogger(__name__)

class UserPage(BasePage):
    """Page object for user management operations."""
    
    def __init__(self, page: Page, app_config: dict):
        """Initialize the user page."""
        super().__init__(page, app_config)
        self.base_url = f"{self.app_config['ui_url']}/#/users"
        
    def navigate(self):
        """Navigate to the users page."""
        self.page.goto(self.base_url)
        self.page.wait_for_selector('.users-list', timeout=self.app_config["test_timeout"])
        self.page.wait_for_network_idle()
        return self

    def get_users_list(self):
        """Get all user rows from the list."""
        return self.page.locator('.user-list-row').all()

    def create_user(self, username, email, password, is_admin=False, is_active=True):
        """Create a new user with the provided details."""
        # Navigate to user page if not already there
        if not self.page.url.endswith('/users'):
            self.navigate()
            
        # Click the 'Add User' button
        self.page.click('[data-test="add-user-button"]')
        
        # Fill the form
        self.page.fill('[data-test="username-input"]', username)
        self.page.fill('[data-test="email-input"]', email)
        self.page.fill('[data-test="password-input"]', password)
        self.page.fill('[data-test="confirm-password-input"]', password)
        
        # Toggle admin status if needed
        if is_admin:
            self.page.click('[data-test="admin-toggle"]')
            
        # Toggle active status if needed
        if not is_active:
            self.page.click('[data-test="active-toggle"]')
            
        # Submit the form
        self.page.click('[data-test="submit-user-button"]')
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check for success message
        success_message = self.page.locator('.success-notification')
        try:
            expect(success_message).to_be_visible(timeout=5000)
            logger.info(f"User {username} created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create user {username}: {str(e)}")
            return False
            
    def edit_user(self, username, new_data):
        """Edit an existing user."""
        # Navigate to user page if not already there
        if not self.page.url.endswith('/users'):
            self.navigate()
            
        # Click edit button for the user
        self.page.click(f"[data-test='edit-user-{username}']")
        
        # Update fields that are provided
        if 'email' in new_data:
            self.page.fill('[data-test="email-input"]', new_data['email'])
            
        if 'password' in new_data:
            self.page.fill('[data-test="password-input"]', new_data['password'])
            self.page.fill('[data-test="confirm-password-input"]', new_data['password'])
            
        if 'is_admin' in new_data:
            current_state = self.page.is_checked('[data-test="admin-toggle"]')
            if current_state != new_data['is_admin']:
                self.page.click('[data-test="admin-toggle"]')
                
        if 'is_active' in new_data:
            current_state = self.page.is_checked('[data-test="active-toggle"]')
            if current_state != new_data['is_active']:
                self.page.click('[data-test="active-toggle"]')
                
        # Submit the form
        self.page.click('[data-test="submit-user-button"]')
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check for success message
        success_message = self.page.locator('.success-notification')
        try:
            expect(success_message).to_be_visible(timeout=5000)
            logger.info(f"User {username} updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update user {username}: {str(e)}")
            return False
    
    def delete_user(self, username):
        """Delete a user by username."""
        # Navigate to user page if not already there
        if not self.page.url.endswith('/users'):
            self.navigate()
            
        # Click delete button for the user
        self.page.click(f"[data-test='delete-user-{username}']")
        
        # Confirm deletion in the modal
        self.page.click("[data-test='confirm-delete-button']")
        
        # Wait for network idle to ensure the request completes
        self.page.wait_for_network_idle()
        
        # Check for success message
        success_message = self.page.locator('.success-notification')
        try:
            expect(success_message).to_be_visible(timeout=5000)
            logger.info(f"User {username} deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to delete user {username}: {str(e)}")
            return False
    
    def view_user_details(self, username):
        """View details of a specific user."""
        # Navigate to user page if not already there
        if not self.page.url.endswith('/users'):
            self.navigate()
            
        # Click on the user row or details button
        self.page.click(f"[data-test='view-user-{username}']")
        
        # Wait for user details to load
        self.page.wait_for_selector('.user-details', timeout=5000)
        
        # Return details if needed
        return {
            'username': self.page.locator('[data-test="detail-username"]').text_content(),
            'email': self.page.locator('[data-test="detail-email"]').text_content(),
            'is_admin': self.page.locator('[data-test="detail-is-admin"]').text_content() == 'Yes',
            'is_active': self.page.locator('[data-test="detail-is-active"]').text_content() == 'Active'
        }
    
    def get_error_message(self):
        """Get the error message if present."""
        error = self.page.locator('.error-notification')
        if error.count() > 0:
            return error.first.text_content()
        return None
        
    def get_validation_errors(self):
        """Get all validation error messages."""
        errors = self.page.locator('.field-error').all()
        return [error.text_content() for error in errors]
        
    def edit_profile(self):
        """Navigate to the profile editing page."""
        # Click on the user menu
        self.page.click('[data-test="user-menu"]')
        
        # Click on the profile option
        self.page.click('[data-test="profile-option"]')
        
        # Wait for the profile page to load
        self.page.wait_for_selector('.profile-form', timeout=5000)
        
        return self 