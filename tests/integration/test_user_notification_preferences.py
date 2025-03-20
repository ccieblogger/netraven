import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

from netraven.web.app import app
from netraven.web.db import get_db
from netraven.web.models.user import User
from netraven.web.schemas.user import UserCreate, NotificationPreferences, UpdateNotificationPreferences
from netraven.web.crud.user import create_user, get_user_by_username

from tests.utils.db_init import get_test_db_session
from tests.utils.test_helpers import get_auth_headers


@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session():
    """Database session fixture."""
    db = next(get_test_db_session())
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user with default notification preferences."""
    # Create test user if it doesn't exist
    username = "testuser"
    email = "testuser@example.com"
    
    user = get_user_by_username(db_session, username)
    if not user:
        user_data = UserCreate(
            username=username,
            email=email,
            password="TestPassword123",
            full_name="Test User",
            is_active=True,
            is_admin=False,
            notification_preferences=NotificationPreferences(
                email_notifications=True,
                email_on_job_completion=True,
                email_on_job_failure=True,
                notification_frequency="immediate"
            )
        )
        user = create_user(db_session, user_data)
    
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """Create an admin user."""
    # Create admin user if it doesn't exist
    username = "adminuser"
    email = "admin@example.com"
    
    user = get_user_by_username(db_session, username)
    if not user:
        user_data = UserCreate(
            username=username,
            email=email,
            password="AdminPassword123",
            full_name="Admin User",
            is_active=True,
            is_admin=True,
            notification_preferences=NotificationPreferences(
                email_notifications=True,
                email_on_job_completion=True,
                email_on_job_failure=True,
                notification_frequency="daily"
            )
        )
        user = create_user(db_session, user_data)
    
    return user


def test_get_user_with_notification_preferences(client, test_user, admin_user, db_session):
    """Test retrieving a user includes notification preferences."""
    # Get auth token for admin
    headers = get_auth_headers(client, admin_user.username, "AdminPassword123")
    
    # Get user by ID
    response = client.get(f"/api/users/{test_user.username}", headers=headers)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check notification preferences exist and have correct values
    assert "notification_preferences" in data
    preferences = data["notification_preferences"]
    assert preferences["email_notifications"] is True
    assert preferences["email_on_job_completion"] is True
    assert preferences["email_on_job_failure"] is True
    assert preferences["notification_frequency"] == "immediate"


def test_update_notification_preferences(client, test_user, db_session):
    """Test updating notification preferences."""
    # Get auth token for test user
    headers = get_auth_headers(client, test_user.username, "TestPassword123")
    
    # Update notification preferences
    update_data = {
        "email_notifications": True,
        "email_on_job_completion": False,  # Changed
        "email_on_job_failure": True,
        "notification_frequency": "daily"   # Changed from immediate
    }
    
    response = client.patch(
        f"/api/users/{test_user.username}/notification-preferences",
        json=update_data,
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check notification preferences were updated
    preferences = data["notification_preferences"]
    assert preferences["email_notifications"] is True
    assert preferences["email_on_job_completion"] is False  # Updated
    assert preferences["email_on_job_failure"] is True
    assert preferences["notification_frequency"] == "daily"  # Updated
    
    # Verify DB was updated
    db_session.refresh(test_user)
    db_user = get_user_by_username(db_session, test_user.username)
    assert db_user.notification_preferences["email_on_job_completion"] is False
    assert db_user.notification_preferences["notification_frequency"] == "daily"


def test_admin_can_update_other_user_preferences(client, test_user, admin_user, db_session):
    """Test that admin can update another user's notification preferences."""
    # Get auth token for admin
    headers = get_auth_headers(client, admin_user.username, "AdminPassword123")
    
    # Update test user's notification preferences
    update_data = {
        "email_notifications": False,  # Changed
        "email_on_job_completion": True,
        "email_on_job_failure": False,  # Changed
        "notification_frequency": "hourly"  # Changed
    }
    
    response = client.patch(
        f"/api/users/{test_user.username}/notification-preferences",
        json=update_data,
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check notification preferences were updated
    preferences = data["notification_preferences"]
    assert preferences["email_notifications"] is False
    assert preferences["email_on_job_completion"] is True
    assert preferences["email_on_job_failure"] is False
    assert preferences["notification_frequency"] == "hourly"


def test_non_admin_cannot_update_other_user_preferences(client, test_user, admin_user, db_session):
    """Test that non-admin users cannot update another user's notification preferences."""
    # Get auth token for test user (non-admin)
    headers = get_auth_headers(client, test_user.username, "TestPassword123")
    
    # Try to update admin user's notification preferences
    update_data = {
        "email_notifications": False,
        "email_on_job_completion": False,
        "email_on_job_failure": False,
        "notification_frequency": "hourly"
    }
    
    response = client.patch(
        f"/api/users/{admin_user.username}/notification-preferences",
        json=update_data,
        headers=headers
    )
    
    # Verify response - should be forbidden
    assert response.status_code == 403
    
    # Verify admin preferences were not changed
    db_session.refresh(admin_user)
    assert admin_user.notification_preferences["email_notifications"] is True
    assert admin_user.notification_preferences["notification_frequency"] == "daily"


def test_invalid_notification_frequency(client, test_user, db_session):
    """Test validation for invalid notification frequency."""
    # Get auth token for test user
    headers = get_auth_headers(client, test_user.username, "TestPassword123")
    
    # Try to update with invalid frequency
    update_data = {
        "email_notifications": True,
        "email_on_job_completion": True,
        "email_on_job_failure": True,
        "notification_frequency": "invalid_value"  # Invalid
    }
    
    response = client.patch(
        f"/api/users/{test_user.username}/notification-preferences",
        json=update_data,
        headers=headers
    )
    
    # Verify response - should be validation error
    assert response.status_code == 422
    
    # Verify user preferences were not changed
    db_session.refresh(test_user)
    assert test_user.notification_preferences["notification_frequency"] != "invalid_value"


def test_partial_preference_update(client, test_user, db_session):
    """Test that partial updates work correctly."""
    # Get auth token for test user
    headers = get_auth_headers(client, test_user.username, "TestPassword123")
    
    # Set initial state
    update_data = {
        "email_notifications": True,
        "email_on_job_completion": True,
        "email_on_job_failure": True,
        "notification_frequency": "immediate"
    }
    
    client.patch(
        f"/api/users/{test_user.username}/notification-preferences",
        json=update_data,
        headers=headers
    )
    
    # Now do a partial update - only update frequency
    partial_update = {
        "notification_frequency": "hourly"
    }
    
    response = client.patch(
        f"/api/users/{test_user.username}/notification-preferences",
        json=partial_update,
        headers=headers
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    
    # Check that only frequency was updated, other settings preserved
    preferences = data["notification_preferences"]
    assert preferences["email_notifications"] is True  # Unchanged
    assert preferences["email_on_job_completion"] is True  # Unchanged
    assert preferences["email_on_job_failure"] is True  # Unchanged
    assert preferences["notification_frequency"] == "hourly"  # Updated
    
    # Verify DB was updated correctly
    db_session.refresh(test_user)
    assert test_user.notification_preferences["email_notifications"] is True
    assert test_user.notification_preferences["notification_frequency"] == "hourly" 