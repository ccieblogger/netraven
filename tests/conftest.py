"""
Pytest fixtures for NetRaven tests.

This module contains pytest fixtures that are used across multiple test files.
"""

import os
import sys
import tempfile
import pytest
import requests
from pathlib import Path

# Add the parent directory to the path so we can import the application
sys.path.insert(0, str(Path(__file__).parent.parent))

# Token store is initialized at import time
import netraven.core.token_store

# Conditionally import TestClient only if httpx is available
try:
    from fastapi.testclient import TestClient
    FASTAPI_TEST_CLIENT_AVAILABLE = True
except ImportError:
    FASTAPI_TEST_CLIENT_AVAILABLE = False
    print("WARNING: fastapi.testclient not available - some tests may be skipped")

# Import conditionally to allow tests to run even if some dependencies are missing
try:
    from netraven.web.database import Base
    from netraven.web import app
    from netraven.web.models.user import User
    from netraven.web.models.device import Device
    from netraven.web.models.backup import Backup
    from netraven.core.config import get_env, is_test_env, load_config
    from netraven.web.database import get_db
    DATABASE_IMPORTS_AVAILABLE = True
except ImportError as e:
    DATABASE_IMPORTS_AVAILABLE = False
    print(f"WARNING: Database imports failed - some tests may be skipped: {str(e)}")

try:
    from passlib.context import CryptContext
    # Password context for hashing test passwords
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    PASSWORD_CONTEXT_AVAILABLE = True
except ImportError:
    PASSWORD_CONTEXT_AVAILABLE = False
    print("WARNING: passlib not available - some tests may be skipped")

@pytest.fixture(scope="session")
def app_config():
    """Get application configuration for tests."""
    # Environment-specific configuration
    env = get_env()
    
    # Print environment info for debugging
    print(f"Test environment: {env}")
    
    # Set default values
    config = {
        "api_url": os.environ.get("TEST_API_URL", "http://localhost:8000"),
        "ui_url": os.environ.get("TEST_UI_URL", "http://localhost:8080"),
        "admin_user": os.environ.get("TEST_ADMIN_USER", "admin"),
        "admin_password": os.environ.get("TEST_ADMIN_PASSWORD", "NetRaven"),
    }
    
    # Add any additional configuration if needed
    app_config = load_config()
    if "web" in app_config:
        if "host" in app_config["web"] and "port" in app_config["web"]:
            config["api_url"] = f"http://{app_config['web']['host']}:{app_config['web']['port']}"
    
    return config


@pytest.fixture
def api_token(app_config):
    """Get a valid API token for testing."""
    try:
        response = requests.post(
            f"{app_config['api_url']}/api/auth/token",
            json={
                "username": app_config["admin_user"],
                "password": app_config["admin_password"]
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"]
    except Exception as e:
        pytest.skip(f"Could not obtain API token: {str(e)}")


@pytest.fixture
def regular_user_token(app_config, api_token):
    """Get a regular (non-admin) user token for testing."""
    # This requires the admin token to create a regular user first
    api_url = app_config['api_url']
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a regular user
    import uuid
    username = f"test-regular-{uuid.uuid4().hex[:8]}"
    
    user_data = {
        "username": username,
        "email": f"{username}@example.com",
        "full_name": "Regular Test User",
        "password": "Password123!",
        "is_active": True,
        "permissions": ["read:devices"]
    }
    
    try:
        # Create the user
        create_response = requests.post(
            f"{api_url}/api/users",
            headers=headers,
            json=user_data
        )
        create_response.raise_for_status()
        user_id = create_response.json()["id"]
        
        # Get token for the new user
        token_response = requests.post(
            f"{api_url}/api/auth/token",
            json={"username": username, "password": "Password123!"}
        )
        token_response.raise_for_status()
        token = token_response.json()["access_token"]
        
        yield token
        
        # Clean up the user
        requests.delete(f"{api_url}/api/users/{user_id}", headers=headers)
    except Exception as e:
        pytest.skip(f"Could not create regular user token: {str(e)}")


# Conditionally define database fixtures only if imports are available
if DATABASE_IMPORTS_AVAILABLE:
    @pytest.fixture
    def test_db():
        """Create a test database."""
        # Create a temporary file for the SQLite database
        db_file = tempfile.NamedTemporaryFile(suffix=".db")
        
        # Create the SQLite URL
        SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file.name}"
        
        # Create the engine
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
        )
        
        # Create the tables
        Base.metadata.create_all(bind=engine)
        
        # Create a session
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Yield the session and engine
        yield TestingSessionLocal, engine
        
        # Clean up
        Base.metadata.drop_all(bind=engine)
        db_file.close()

    @pytest.fixture
    def db_session(test_db):
        """Create a database session for testing."""
        TestingSessionLocal, _ = test_db
        
        # Create a session
        db = TestingSessionLocal()
        
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def client(db_session):
        """Create a test client for the FastAPI application."""
        if not FASTAPI_TEST_CLIENT_AVAILABLE:
            pytest.skip("FastAPI TestClient not available")
            
        # Override the get_db dependency to use our test database
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
                
        app.dependency_overrides[get_db] = override_get_db
        
        # Create a test client
        with TestClient(app) as client:
            yield client
            
        # Clear the dependency override
        app.dependency_overrides = {}

@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    # Create a user
    user = User(
        id="00000000-0000-0000-0000-000000000001",
        username="testuser",
        email="test@example.com",
        hashed_password=pwd_context.hash("password"),
        full_name="Test User",
        is_active=True,
        is_admin=False
    )
    
    # Add the user to the database
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def test_admin(db_session):
    """Create a test admin user."""
    # Create an admin user
    admin = User(
        id="00000000-0000-0000-0000-000000000002",
        username="admin",
        email="admin@example.com",
        hashed_password=pwd_context.hash("adminpassword"),
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    
    # Add the admin to the database
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    return admin

@pytest.fixture
def test_device(db_session, test_user):
    """Create a test device."""
    # Create a device
    device = Device(
        id="00000000-0000-0000-0000-000000000003",
        hostname="testrouter",
        ip_address="192.168.1.1",
        device_type="cisco_ios",
        port=22,
        username="cisco",
        password="cisco",
        description="Test Router",
        enabled=True,
        owner_id=test_user.id
    )
    
    # Add the device to the database
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    
    return device

@pytest.fixture
def test_backup(db_session, test_device):
    """Create a test backup."""
    # Create a backup
    backup = Backup(
        id="00000000-0000-0000-0000-000000000004",
        device_id=test_device.id,
        version="1.0",
        file_path="/backups/testrouter_config.txt",
        file_size=1024,
        status="complete",
        comment="Test backup",
        content_hash="abcdef1234567890",
        is_automatic=True
    )
    
    # Add the backup to the database
    db_session.add(backup)
    db_session.commit()
    db_session.refresh(backup)
    
    return backup

@pytest.fixture
def token_headers(client, test_user):
    """Get authentication headers with a valid token."""
    # Log in to get a token
    response = client.post(
        "/api/auth/token",
        data={"username": test_user.username, "password": "password"}
    )
    
    # Get the token from the response
    token = response.json()["access_token"]
    
    # Return the headers
    return {"Authorization": f"Bearer {token}"} 