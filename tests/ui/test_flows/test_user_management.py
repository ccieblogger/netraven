"""
Tests for user management functionality.
"""
import uuid
import pytest
from playwright.sync_api import expect
from tests.ui.pages.user_page import UserPage

@pytest.fixture
def user_page(page, authenticated_page, app_config):
    """Returns an instance of UserPage."""
    return UserPage(authenticated_page, app_config["ui_url"])

@pytest.fixture
def test_user_data():
    """Generate unique test user data."""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"testuser_{unique_id}@example.com",
        "password": "Test@12345"
    }

def test_view_users_list(user_page):
    """Test that the users list is displayed."""
    # Navigate to users page
    user_page.navigate()
    
    # Verify that the users list is visible
    expect(user_page.page.locator(".users-list")).to_be_visible()
    
    # Verify that at least the admin user is in the list
    expect(user_page.page.locator("[data-test='user-row-admin']")).to_be_visible()

def test_create_user(user_page, test_user_data):
    """Test creating a new user."""
    # Navigate to users page
    user_page.navigate()
    
    # Create a new test user
    success = user_page.create_user(
        test_user_data["username"],
        test_user_data["email"],
        test_user_data["password"]
    )
    
    # Verify that user creation was successful
    assert success, "User creation failed"
    
    # Verify that the user appears in the list
    expect(user_page.page.locator(f"[data-test='user-row-{test_user_data['username']}']")).to_be_visible()
    
    # Clean up - delete the user
    user_page.delete_user(test_user_data["username"])

def test_create_user_validation(user_page):
    """Test validation errors when creating a user with invalid data."""
    # Navigate to users page
    user_page.navigate()
    
    # Click add user button
    user_page.page.click('[data-test="add-user-button"]')
    
    # Try to submit without filling required fields
    user_page.page.click('[data-test="submit-user-button"]')
    
    # Verify validation errors
    validation_errors = user_page.get_validation_errors()
    assert len(validation_errors) > 0, "No validation errors displayed"
    
    # Verify specific validation messages for required fields
    error_texts = [error.lower() for error in validation_errors]
    assert any("username" in error for error in error_texts), "No username validation error"
    assert any("password" in error for error in error_texts), "No password validation error"

def test_edit_user(user_page, test_user_data):
    """Test editing an existing user."""
    # First create a user to edit
    user_page.navigate()
    user_page.create_user(
        test_user_data["username"],
        test_user_data["email"],
        test_user_data["password"]
    )
    
    # Generate new email for the edit
    new_email = f"edited-{test_user_data['email']}"
    
    # Edit the user
    success = user_page.edit_user(test_user_data["username"], {
        "email": new_email
    })
    
    # Verify that the edit was successful
    assert success, "User edit failed"
    
    # View the user details to verify changes
    user_details = user_page.view_user_details(test_user_data["username"])
    assert user_details["email"] == new_email, "Email was not updated"
    
    # Clean up - delete the user
    user_page.delete_user(test_user_data["username"])

def test_delete_user(user_page, test_user_data):
    """Test deleting a user."""
    # First create a user to delete
    user_page.navigate()
    user_page.create_user(
        test_user_data["username"],
        test_user_data["email"],
        test_user_data["password"]
    )
    
    # Delete the user
    success = user_page.delete_user(test_user_data["username"])
    
    # Verify that the delete was successful
    assert success, "User deletion failed"
    
    # Verify that the user is no longer in the list
    user_row = user_page.page.locator(f"[data-test='user-row-{test_user_data['username']}']")
    expect(user_row).to_have_count(0)

def test_edit_profile(user_page):
    """Test that the profile editing form is displayed."""
    # Navigate to profile page
    user_page.edit_profile()
    
    # Verify that the profile form is visible
    expect(user_page.page.locator(".profile-form")).to_be_visible()
    
    # Verify that the username field contains admin
    username_field = user_page.page.locator('[data-test="profile-username"]')
    expect(username_field).to_contain_text("admin")

def test_create_duplicate_user(user_page, test_user_data):
    """Test creating a user with a duplicate username."""
    # First create a user
    user_page.navigate()
    user_page.create_user(
        test_user_data["username"],
        test_user_data["email"],
        test_user_data["password"]
    )
    
    # Try to create another user with the same username but different email
    duplicate_result = user_page.create_user(
        test_user_data["username"],
        f"different-{test_user_data['email']}",
        test_user_data["password"]
    )
    
    # Verify that user creation failed
    assert not duplicate_result, "Duplicate user creation should fail"
    
    # Verify error message
    error_message = user_page.get_error_message()
    assert error_message is not None
    assert "username" in error_message.lower(), "Error should mention username"
    
    # Clean up - delete the original user
    user_page.delete_user(test_user_data["username"])

def test_create_user_with_invalid_password(user_page, test_user_data):
    """Test creating a user with an invalid password."""
    # Navigate to users page
    user_page.navigate()
    
    # Click add user button
    user_page.page.click('[data-test="add-user-button"]')
    
    # Fill form with invalid password (too short)
    user_page.page.fill('[data-test="username-input"]', test_user_data["username"])
    user_page.page.fill('[data-test="email-input"]', test_user_data["email"])
    user_page.page.fill('[data-test="password-input"]', "short")
    user_page.page.fill('[data-test="confirm-password-input"]', "short")
    
    # Submit the form
    user_page.page.click('[data-test="submit-user-button"]')
    
    # Verify validation errors for password
    validation_errors = user_page.get_validation_errors()
    assert len(validation_errors) > 0, "No validation errors displayed"
    
    # Check for password complexity error
    error_texts = [error.lower() for error in validation_errors]
    assert any("password" in error for error in error_texts), "No password validation error"

def test_user_permissions(user_page, test_user_data):
    """Test that user permissions can be set and are visible in the UI."""
    # Create a user with admin permissions
    user_page.navigate()
    user_page.create_user(
        test_user_data["username"],
        test_user_data["email"],
        test_user_data["password"],
        is_admin=True
    )
    
    # Verify the user is created and has admin status
    user_details = user_page.view_user_details(test_user_data["username"])
    assert user_details["is_admin"], "User should have admin status"
    
    # Edit user to remove admin status
    user_page.edit_user(test_user_data["username"], {
        "is_admin": False
    })
    
    # Verify admin status is updated
    user_details = user_page.view_user_details(test_user_data["username"])
    assert not user_details["is_admin"], "User should no longer have admin status"
    
    # Clean up - delete the user
    user_page.delete_user(test_user_data["username"]) 