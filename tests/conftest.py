"""
Pytest fixtures for NetRaven tests.

This module contains pytest fixtures that are used across multiple test files.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from passlib.context import CryptContext

# Add the parent directory to the path so we can import the application
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import NetRaven modules
from netraven.web.database import Base
from netraven.web import app
from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.core.config import DEFAULT_CONFIG
from netraven.web.database import get_db

# Password context for hashing test passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@pytest.fixture
def test_db():
    """Create a test database."""
    # Create a temporary file for the SQLite database
    db_file = tempfile.NamedTemporaryFile(suffix=".db")
    
    # Create the SQLite URL
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file.name}"
    
    # Create the engine
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