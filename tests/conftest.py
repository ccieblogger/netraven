"""
Pytest configuration and fixtures.

This module provides common fixtures and configurations for tests.
"""

import os
import sys
import tempfile
import pytest
import requests
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import delete
import uuid

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
    from netraven.web.models.job_log import JobLog
    from netraven.web.models.scheduled_job import ScheduledJob
    from netraven.core.config import get_env, is_test_env, load_config
    from netraven.web.database import get_db
    from netraven.core.services.async_job_logging_service import AsyncJobLoggingService
    from netraven.core.services.async_scheduler_service import AsyncSchedulerService
    from netraven.core.services.async_device_comm_service import AsyncDeviceCommunicationService
    # Ensure asyncpg is imported for PostgreSQL async support
    import asyncpg
    DATABASE_IMPORTS_AVAILABLE = True
except ImportError as e:
    DATABASE_IMPORTS_AVAILABLE = False
    print(f"WARNING: Database imports failed - some tests may be skipped: {str(e)}")

# Load environment variables
load_dotenv()

# Create a session-scoped event loop for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Test configuration
TEST_CONFIG = {
    "api_url": "http://localhost:8000",
    "test_user": {
        "username": "testuser",
        "password": "testpass",
        "email": "test@example.com",
        "full_name": "Test User"
    },
    "test_admin": {
        "username": "admin",
        "password": "adminpass",
        "email": "admin@example.com",
        "full_name": "Admin User"
    }
}

# Conditionally define database fixtures only if imports are available
if DATABASE_IMPORTS_AVAILABLE:
    @pytest.fixture(scope="session")
    async def test_db():
        """
        Create a test database with proper async support.
        
        This implementation addresses the SQLAlchemy NullPool issue by using
        a proper connection pooling strategy for PostgreSQL.
        """
        # Get PostgreSQL connection details from environment
        # In Docker, we always use the postgres service name in a container
        in_container = os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv')
        if in_container or os.getenv("SERVICE_TYPE") == "api" or os.getenv("POSTGRES_HOST"):
            print("Detected Docker environment, using 'postgres' as database host")
            DB_HOST = "postgres"
        else:
            DB_HOST = "localhost"
            
        # Use the same database credentials as the main application
        DB_USER = os.getenv("POSTGRES_USER", "netraven")
        DB_PASS = os.getenv("POSTGRES_PASSWORD", "netraven")
        DB_PORT = os.getenv("POSTGRES_PORT", "5432")
        DB_NAME = os.getenv("POSTGRES_DB", "netraven")
        
        # Create the PostgreSQL URL
        SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        # Log the database connection string (without credentials)
        print(f"Test database: Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}/{DB_NAME}")
        
        # Create the engine with proper pooling setup - no connect_timeout for asyncpg
        engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            poolclass=None,  # Default pool
            echo=False,
            future=True
        )
        
        # Create the tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create a session
        TestingAsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # Yield the session and engine
        yield TestingAsyncSessionLocal, engine
        
        # Clean up
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    @pytest.fixture
    async def db_session(test_db):
        """Create a database session for testing."""
        TestingAsyncSessionLocal, _ = test_db
        
        # Create a session
        async with TestingAsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    @pytest.fixture(autouse=True)
    async def cleanup_test_data(db_session):
        """Clean up test data after each test."""
        yield
        # Clean up all test data
        # Order is important to avoid foreign key constraint violations
        # First clean up tables with foreign keys
        for model in [ScheduledJob, JobLog, Backup]:
            await db_session.execute(delete(model))
        await db_session.commit()
        
        # Then clean up Device which depends on User
        await db_session.execute(delete(Device))
        await db_session.commit()
        
        # Finally clean up User
        await db_session.execute(delete(User))
        await db_session.commit()

    @pytest.fixture
    async def job_logging_service(db_session):
        """Create a job logging service instance."""
        service = AsyncJobLoggingService(db_session=db_session)
        yield service
        # No close() method needed - the service doesn't manage resources directly

    @pytest.fixture
    async def scheduler_service(job_logging_service, db_session):
        """Create a scheduler service instance."""
        service = AsyncSchedulerService(
            job_logging_service=job_logging_service,
            db_session=db_session
        )
        yield service
        await service.stop()

    @pytest.fixture
    async def device_comm_service(job_logging_service, db_session):
        """Create a device communication service instance."""
        service = AsyncDeviceCommunicationService(
            job_logging_service=job_logging_service,
            db_session=db_session
        )
        yield service
        # Service might not have a close method - only call if it exists
        if hasattr(service, 'close') and callable(service.close):
            await service.close()

    @pytest.fixture
    async def test_device_data():
        """Create test device data."""
        return {
            "hostname": "test.example.com",
            "ip_address": "192.168.1.1",
            "device_type": "cisco_ios",
            "port": 22,
            "username": "admin",
            "password": "password",
            "description": "Test Device",
            "enabled": True
        }

    @pytest.fixture
    async def test_job_data():
        """Create test job data."""
        return {
            "name": "Test Job",
            "description": "Test job description",
            "job_type": "backup",
            "schedule": "0 0 * * *",
            "device_ids": ["device-1", "device-2"]
        }

    @pytest.fixture
    async def test_user_data():
        """Create test user data."""
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "full_name": "Test User",
            "is_active": True,
            "is_admin": False
        }

    @pytest.fixture
    async def test_admin_data():
        """Create test admin data."""
        return {
            "username": "admin",
            "email": "admin@example.com",
            "full_name": "Admin User",
            "password_hash": "hashed_admin_password",
            "is_active": True,
            "is_admin": True
        }

    @pytest.fixture
    async def test_user(db_session, test_user_data):
        """Create a test user."""
        user = User(**test_user_data)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_admin(db_session, test_admin_data):
        """Create a test admin user."""
        admin = User(**test_admin_data)
        db_session.add(admin)
        await db_session.commit()
        await db_session.refresh(admin)
        return admin

    @pytest.fixture
    async def test_device(db_session, test_device_data, test_user):
        """Create a test device with a valid owner."""
        # Use the test_user for the owner_id
        device_data = test_device_data.copy()
        device_data["owner_id"] = test_user.id
        
        device = Device(**device_data)
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device

    @pytest.fixture
    async def test_job(db_session, test_job_data):
        """Create a test job."""
        job = ScheduledJob(**test_job_data)
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)
        return job

    @pytest.fixture
    def client(db_session):
        """Create a test client for the FastAPI application."""
        if not FASTAPI_TEST_CLIENT_AVAILABLE:
            pytest.skip("FastAPI TestClient not available")
            
        # Override the get_db dependency to use our test database
        async def override_get_db():
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
    async def test_backup_device(db_session, test_user):
        """Create a test device for backup tests."""
        device = Device(
            hostname="backup-test.example.com",
            ip_address="192.168.1.10",
            device_type="cisco_ios",
            port=22,
            username="admin",
            password="password",
            description="Test device for backups",
            enabled=True,
            owner_id=test_user.id
        )
        db_session.add(device)
        await db_session.commit()
        await db_session.refresh(device)
        return device

    @pytest.fixture
    async def test_backup(db_session, test_backup_device):
        """Create a test backup."""
        backup = Backup(
            version="1.0",
            file_path="/backups/test.cfg",
            file_size=1024,
            status="complete",
            comment="Test backup",
            content_hash="abcdef1234567890",
            is_automatic=True,
            device_id=test_backup_device.id
        )
        db_session.add(backup)
        await db_session.commit()
        await db_session.refresh(backup)
        return backup

# Test client factories
@pytest.fixture
def create_test_client():
    """
    Factory function to create a test client with custom router and principal.
    
    Example usage:
        client = create_test_client(router=my_router, 
                                    principal=mock_admin_principal,
                                    service_path="module.path.get_service",
                                    service_mock=mock_service)
    """
    def _create_client(router, principal=None, service_path=None, service_mock=None, db=None):
        app = FastAPI()
        app.include_router(router)
        
        # Override dependencies
        if db is None:
            db = MagicMock(spec=AsyncSession)
        app.dependency_overrides[get_db] = lambda: db
        
        # Override dependencies if principal is provided
        if principal is not None:
            app.dependency_overrides[get_current_principal] = lambda: principal
        
        # Mock service if provided
        if service_path and service_mock:
            with patch(service_path, return_value=service_mock):
                yield TestClient(app)
        else:
            yield TestClient(app)
    
    return _create_client

def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--api-url",
        default=None,
        help="API URL for integration tests"
    )
    parser.addoption(
        "--admin-username",
        default=None,
        help="Admin username for integration tests"
    )
    parser.addoption(
        "--admin-password",
        default=None,
        help="Admin password for integration tests"
    )


@pytest.fixture(scope="session")
def app_config(request):
    """
    Fixture to provide application configuration for tests.
    
    Loads configuration from environment variables or pytest options.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Get configuration from pytest options or environment variables
    api_url = request.config.getoption("--api-url") or os.environ.get("NETRAVEN_API_URL", "http://localhost:8000")
    admin_username = request.config.getoption("--admin-username") or os.environ.get("NETRAVEN_ADMIN_USERNAME", "admin")
    admin_password = request.config.getoption("--admin-password") or os.environ.get("NETRAVEN_ADMIN_PASSWORD", "admin")
    
    return {
        "api_url": api_url.rstrip("/"),  # Remove trailing slash if present
        "admin_username": admin_username,
        "admin_password": admin_password
    }


@pytest.fixture(scope="session")
def api_token(app_config):
    """
    Fixture to provide an API token for authenticated requests.
    
    Uses the admin credentials from app_config to acquire a token.
    This fixture is critical for testing authenticated endpoints.
    If authentication fails, the test will fail - this indicates
    a real issue with the authentication system that needs to be fixed.
    
    Returns:
        str: Valid API token for authentication
    
    Raises:
        AssertionError: If authentication fails
    """
    try:
        # Use admin credentials to get a real token
        username = app_config.get("admin_user", "admin")
        password = app_config.get("admin_password", "NetRaven")
        
        # Log the attempt for debugging
        print(f"Authenticating with {username} at {app_config['api_url']}")
        
        # Use the create_test_api_token utility
        token = create_test_api_token(
            app_config["api_url"],
            username,
            password
        )
        
        if not token or len(token) < 10:
            raise AssertionError(f"Invalid token received: {token}")
            
        print(f"Successfully obtained authentication token: {token[:10]}...")
        return token
    except Exception as e:
        # Instead of skipping tests, fail them with a clear error message
        # This approach treats authentication failure as a real issue
        pytest.fail(f"AUTHENTICATION FAILURE: Could not obtain API token with admin credentials. Error: {str(e)}")


@pytest.fixture(scope="function")
def verify_api_available(app_config):
    """
    Fixture to verify that the API is available before running tests.
    
    Raises:
        pytest.skip: If the API is not available
    """
    try:
        response = requests.get(f"{app_config['api_url']}/api/health")
        if response.status_code != 200:
            pytest.skip(f"API is not available: Status code {response.status_code}")
    except requests.RequestException as e:
        pytest.skip(f"API is not available: {str(e)}")
    
    return True


@pytest.fixture(scope="session", autouse=True)
def delay_between_tests():
    """Add a small delay between tests to prevent API rate limiting."""
    yield
    time.sleep(0.1)  # 100ms delay


@pytest.fixture(scope="function")
def test_tag(app_config, api_token, request):
    """
    Fixture to create a test tag and clean it up after the test.
    
    Returns:
        dict: The created tag data
    """
    from tests.utils.api_test_utils import create_test_tag, cleanup_test_resources
    
    # Create a tag
    tag = create_test_tag(app_config["api_url"], api_token)
    
    # Add finalizer to clean up after test
    resources_to_cleanup = {"tags": [tag["id"]]}
    request.addfinalizer(
        lambda: cleanup_test_resources(app_config["api_url"], api_token, resources_to_cleanup)
    )
    
    return tag


@pytest.fixture(scope="function")
def test_device(app_config, api_token, request):
    """
    Fixture to create a test device and clean it up after the test.
    
    Returns:
        dict: The created device data
    """
    from tests.utils.api_test_utils import create_test_device, cleanup_test_resources
    
    # Create a device
    device = create_test_device(app_config["api_url"], api_token)
    
    # Add finalizer to clean up after test
    resources_to_cleanup = {"devices": [device["id"]]}
    request.addfinalizer(
        lambda: cleanup_test_resources(app_config["api_url"], api_token, resources_to_cleanup)
    )
    
    return device


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
def regular_user_token(app_config, api_token):
    """Get a regular (non-admin) user token for testing."""
    # This requires the admin token to create a regular user first
    api_url = app_config['api_url']
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Create a regular user
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


# Core test fixtures
@pytest.fixture
def app_config():
    """Provide test configuration."""
    return {
        "api_url": os.environ.get("TEST_API_URL", "http://localhost:8000"),
        "admin_username": os.environ.get("TEST_ADMIN_USERNAME", "admin"),
        "admin_password": os.environ.get("TEST_ADMIN_PASSWORD", "NetRaven")
    }


@pytest.fixture
def api_token(app_config):
    """
    Get an API token for authenticated requests.
    
    This uses the real API to get a token, unlike the mock version.
    """
    try:
        from tests.utils.api_test_utils import create_test_api_token
        print(f"Trying to get token from {app_config['api_url']} with {app_config['admin_username']}")
        token = create_test_api_token(
            app_config["api_url"],
            app_config["admin_username"],
            app_config["admin_password"]
        )
        print(f"Successfully obtained token: {token[:10]}...")
        return token
    except Exception as e:
        print(f"ERROR getting token: {str(e)}")
        pytest.skip(f"Could not obtain API token: {str(e)}")
        return "mock-api-token"  # Fallback to mock if needed


# Database fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=AsyncSession)


# Principal fixtures
@pytest.fixture
def mock_admin_principal():
    """Create a mock admin user principal."""
    principal = MagicMock(spec=UserPrincipal)
    principal.username = "admin"
    principal.is_admin = True
    principal.has_scope.return_value = True
    return principal


@pytest.fixture
def mock_user_principal():
    """Create a mock regular user principal."""
    principal = MagicMock(spec=UserPrincipal)
    principal.username = "regular_user"
    principal.is_admin = False
    
    # Configure the has_scope method to check the scope
    def has_scope_side_effect(scope):
        # Common read scopes
        if scope in ["read:devices", "devices:read",
                     "read:tags", "tags:read",
                     "read:audit-logs", "audit-logs:read"]:
            return True
        # Common write scopes - regular user doesn't have write access
        elif scope in ["write:devices", "devices:write",
                      "write:tags", "tags:write",
                      "write:audit-logs", "audit-logs:write"]:
            return False
        return False
    
    principal.has_scope.side_effect = has_scope_side_effect
    return principal


# Test client factories
@pytest.fixture
def admin_client_factory(mock_admin_principal, mock_db, create_test_client):
    """Factory for creating admin test clients for different routers."""
    def _create_admin_client(router, service_path=None, service_mock=None):
        return create_test_client(
            router=router,
            principal=mock_admin_principal,
            service_path=service_path,
            service_mock=service_mock,
            db=mock_db
        )
    
    return _create_admin_client


@pytest.fixture
def user_client_factory(mock_user_principal, mock_db, create_test_client):
    """Factory for creating regular user test clients for different routers."""
    def _create_user_client(router, service_path=None, service_mock=None):
        return create_test_client(
            router=router,
            principal=mock_user_principal,
            service_path=service_path,
            service_mock=service_mock,
            db=mock_db
        )
    
    return _create_user_client


@pytest.fixture
def no_auth_client_factory(mock_db, create_test_client):
    """Factory for creating unauthenticated test clients for different routers."""
    def _create_no_auth_client(router, service_path=None, service_mock=None):
        return create_test_client(
            router=router,
            principal=None,
            service_path=service_path,
            service_mock=service_mock,
            db=mock_db
        )
    
    return _create_no_auth_client


# Mock service factories
@pytest.fixture
def create_mock_device_service():
    """Factory to create a mock device service with customizable behavior."""
    def _create_service(devices=None, device=None):
        service = MagicMock()
        
        # Default mock data
        default_devices = [
            {"id": "device-1", "hostname": "router1", "ip_address": "192.168.1.1", "device_type": "cisco_ios"},
            {"id": "device-2", "hostname": "router2", "ip_address": "192.168.1.2", "device_type": "cisco_ios"}
        ]
        
        default_device = {
            "id": "device-1", 
            "hostname": "router1", 
            "ip_address": "192.168.1.1", 
            "device_type": "cisco_ios"
        }
        
        # Configure the mock service behavior
        service.get_devices.return_value = devices or default_devices
        service.get_device_by_id.return_value = device or default_device
        service.create_device.return_value = {
            "id": "new-device", 
            "hostname": "new-router", 
            "ip_address": "192.168.1.10", 
            "device_type": "cisco_ios"
        }
        service.update_device.return_value = {
            "id": "device-1", 
            "hostname": "updated-router", 
            "ip_address": "192.168.1.1", 
            "device_type": "cisco_ios"
        }
        service.delete_device.return_value = True
        
        return service
    
    return _create_service


@pytest.fixture
def create_mock_tag_service():
    """Factory to create a mock tag service with customizable behavior."""
    def _create_service(tags=None, tag=None):
        service = MagicMock()
        
        # Default mock data
        default_tags = [
            {"id": "tag-1", "name": "Production", "description": "Production devices", "color": "#FF0000"},
            {"id": "tag-2", "name": "Development", "description": "Development devices", "color": "#00FF00"}
        ]
        
        default_tag = {
            "id": "tag-1", 
            "name": "Production", 
            "description": "Production devices", 
            "color": "#FF0000"
        }
        
        # Configure the mock service behavior
        service.get_tags.return_value = tags or default_tags
        service.get_tag_by_id.return_value = tag or default_tag
        service.create_tag.return_value = {
            "id": "new-tag", 
            "name": "Test", 
            "description": "Test devices", 
            "color": "#0000FF"
        }
        service.update_tag.return_value = {
            "id": "tag-1", 
            "name": "Updated", 
            "description": "Updated tag", 
            "color": "#FF0000"
        }
        service.delete_tag.return_value = True
        service.get_devices_by_tag_id.return_value = [
            {"id": "device-1", "hostname": "router1", "ip_address": "192.168.1.1", "device_type": "cisco_ios"}
        ]
        
        return service
    
    return _create_service


@pytest.fixture
def create_mock_audit_logs_service():
    """Factory to create a mock audit logs service with customizable behavior."""
    def _create_service(logs=None, log=None):
        service = MagicMock()
        
        # Default mock data
        default_logs = [
            {
                "id": "log-1",
                "timestamp": "2023-03-10T12:00:00",
                "user_id": "user-1",
                "username": "admin",
                "action": "create",
                "resource_type": "device",
                "resource_id": "device-1",
                "details": {"ip_address": "192.168.1.100"}
            },
            {
                "id": "log-2",
                "timestamp": "2023-03-09T12:00:00",
                "user_id": "user-2",
                "username": "john",
                "action": "update",
                "resource_type": "tag",
                "resource_id": "tag-1",
                "details": {"ip_address": "192.168.1.101"}
            }
        ]
        
        default_log = {
            "id": "log-1",
            "timestamp": "2023-03-10T12:00:00",
            "user_id": "user-1",
            "username": "admin",
            "action": "create",
            "resource_type": "device",
            "resource_id": "device-1",
            "details": {"ip_address": "192.168.1.100"}
        }
        
        # Configure the mock service behavior
        service.get_audit_logs.return_value = logs or default_logs
        service.get_audit_log_by_id.return_value = log or default_log
        service.create_audit_log.return_value = {
            "id": "new-log",
            "timestamp": "2023-03-10T12:00:00",
            "user_id": "user-1",
            "username": "admin",
            "action": "delete",
            "resource_type": "user",
            "resource_id": "user-3",
            "details": {"ip_address": "192.168.1.102"}
        }
        service.get_audit_logs_by_user.return_value = [default_logs[0]]
        service.get_audit_logs_by_resource.return_value = [default_logs[1]]
        
        return service
    
    return _create_service

@pytest.fixture
def mock_service_factory():
    """Create a mock service factory."""
    return MagicMock()

@pytest.fixture
def mock_job_logging_service():
    """Create a mock job logging service."""
    return MagicMock()

@pytest.fixture
def mock_scheduler_service():
    """Create a mock scheduler service."""
    return MagicMock()

@pytest.fixture
def mock_device_comm_service():
    """Create a mock device communication service."""
    return MagicMock()

@pytest.fixture
def test_user_data():
    """Create test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "full_name": "Test User",
        "is_active": True,
        "is_admin": False
    }

@pytest.fixture
def test_job_data():
    """Create test job data."""
    return {
        "job_type": "backup",
        "device_id": "test-device-id",
        "parameters": {
            "backup_type": "config",
            "destination": "local"
        },
        "schedule": {
            "type": "once",
            "start_time": "2024-01-01T00:00:00Z"
        }
    } 