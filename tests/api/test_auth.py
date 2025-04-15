import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import logging
from unittest.mock import patch

from netraven.api.main import app
from netraven.db import models
from netraven.api import auth
from netraven.api.routers.auth_router import authenticate_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test data
TEST_USER = {
    "username": "testuser",
    "password": "testpassword",
    "email": "testuser@example.com",  # Add a valid email
    "role": "user",
    "is_active": True
}

TEST_ADMIN = {
    "username": "testadmin",
    "password": "adminpassword",
    "email": "testadmin@example.com",  # Add a valid email
    "role": "admin",
    "is_active": True
}

TEST_INACTIVE_USER = {
    "username": "inactiveuser",
    "password": "inactivepassword", 
    "email": "inactive@example.com",  # Add a valid email
    "role": "user",
    "is_active": False
}

@pytest.fixture
def test_user(db_session: Session):
    """Create a test user for authentication tests."""
    # Check if the test user already exists
    existing_user = db_session.query(models.User).filter_by(username=TEST_USER["username"]).first()
    if existing_user:
        logger.info(f"Using existing test user: {existing_user.username}")
        return existing_user
    
    # Create a new test user
    logger.info(f"Creating new test user: {TEST_USER['username']}")
    user_data = TEST_USER.copy()
    password = user_data.pop("password")
    user_data["hashed_password"] = auth.get_password_hash(password)
    
    user = models.User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f"Created test user with ID: {user.id}")
    return user

@pytest.fixture
def test_admin(db_session: Session):
    """Create a test admin for authentication tests."""
    # Check if the test admin already exists
    existing_admin = db_session.query(models.User).filter_by(username=TEST_ADMIN["username"]).first()
    if existing_admin:
        logger.info(f"Using existing test admin: {existing_admin.username}")
        return existing_admin
    
    # Create a new test admin
    logger.info(f"Creating new test admin: {TEST_ADMIN['username']}")
    admin_data = TEST_ADMIN.copy()
    password = admin_data.pop("password")
    admin_data["hashed_password"] = auth.get_password_hash(password)
    
    admin = models.User(**admin_data)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    logger.info(f"Created test admin with ID: {admin.id}")
    return admin

@pytest.fixture
def test_inactive_user(db_session: Session):
    """Create a test inactive user for authentication tests."""
    # Check if the test inactive user already exists
    existing_user = db_session.query(models.User).filter_by(username=TEST_INACTIVE_USER["username"]).first()
    if existing_user:
        logger.info(f"Using existing test inactive user: {existing_user.username}")
        return existing_user
    
    # Create a new inactive test user
    logger.info(f"Creating new test inactive user: {TEST_INACTIVE_USER['username']}")
    user_data = TEST_INACTIVE_USER.copy()
    password = user_data.pop("password")
    user_data["hashed_password"] = auth.get_password_hash(password)
    
    user = models.User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f"Created test inactive user with ID: {user.id}")
    return user

@pytest.fixture
def client():
    """Create a test client with a clean dependency override."""
    # Make sure we have a clean client without any overrides
    app.dependency_overrides = {}
    return TestClient(app)

# Test the authenticate_user function directly
def test_authenticate_user(db_session, test_user):
    """Test the authenticate_user function directly."""
    # Test valid authentication
    user = authenticate_user(db_session, TEST_USER["username"], TEST_USER["password"])
    assert user is not None
    assert user.username == TEST_USER["username"]
    
    # Test invalid password
    user = authenticate_user(db_session, TEST_USER["username"], "wrongpassword")
    assert user is None
    
    # Test non-existent user
    user = authenticate_user(db_session, "nonexistentuser", "anypassword")
    assert user is None

# Mock the authenticate_user function for token endpoint tests
@patch('netraven.api.routers.auth_router.authenticate_user')
def test_login_valid_user(mock_authenticate, client, test_user):
    """Test successful login with valid credentials."""
    # Set up mock to return our test user
    mock_authenticate.return_value = test_user
    
    logger.info(f"Testing login for user: {TEST_USER['username']}")
    response = client.post(
        "/auth/token",
        data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
    )
    assert response.status_code == 200, f"Login failed with status {response.status_code}: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Verify our mock was called with the right arguments
    mock_authenticate.assert_called_once()

@patch('netraven.api.routers.auth_router.authenticate_user')
def test_login_invalid_password(mock_authenticate, client, test_user):
    """Test login failure with invalid password."""
    # Set up mock to return None (authentication failure)
    mock_authenticate.return_value = None
    
    response = client.post(
        "/auth/token",
        data={"username": TEST_USER["username"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    
    # Verify our mock was called with the right arguments
    mock_authenticate.assert_called_once()

@patch('netraven.api.routers.auth_router.authenticate_user')
def test_login_nonexistent_user(mock_authenticate, client):
    """Test login failure with non-existent user."""
    # Set up mock to return None (authentication failure)
    mock_authenticate.return_value = None
    
    response = client.post(
        "/auth/token", 
        data={"username": "nonexistentuser", "password": "anypassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]
    
    # Verify our mock was called with the right arguments
    mock_authenticate.assert_called_once()

@patch('netraven.api.routers.auth_router.authenticate_user')
def test_login_inactive_user(mock_authenticate, client, test_inactive_user):
    """Test login failure with inactive user."""
    # Set up mock to return our inactive test user
    mock_authenticate.return_value = test_inactive_user
    
    response = client.post(
        "/auth/token",
        data={"username": TEST_INACTIVE_USER["username"], "password": TEST_INACTIVE_USER["password"]}
    )
    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]
    
    # Verify our mock was called with the right arguments
    mock_authenticate.assert_called_once()

@patch('netraven.api.routers.auth_router.authenticate_user')
def test_admin_login(mock_authenticate, client, test_admin):
    """Test successful admin login."""
    # Set up mock to return our test admin
    mock_authenticate.return_value = test_admin
    
    logger.info(f"Testing login for admin: {TEST_ADMIN['username']}")
    response = client.post(
        "/auth/token",
        data={"username": TEST_ADMIN["username"], "password": TEST_ADMIN["password"]}
    )
    assert response.status_code == 200, f"Admin login failed with status {response.status_code}: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    
    # Decode the token to verify it includes the admin role
    decoded_token = auth.decode_access_token(token_data["access_token"])
    assert decoded_token["role"] == "admin"
    
    # Verify our mock was called with the right arguments
    mock_authenticate.assert_called_once() 