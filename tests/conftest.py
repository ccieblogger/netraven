import pytest
import os
import subprocess
from sqlalchemy.orm import Session
from sqlalchemy import text # Import text for raw SQL if needed in fixtures

from netraven.db.session import get_db, engine, SessionLocal
from netraven.db import Base
from netraven.db.models import Device, Job # Import necessary models
from tests.api.test_auth import test_user, test_admin, test_inactive_user

# --- Alembic Schema Management Fixture --- 

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Ensures the test database schema is up-to-date via Alembic.
    
    This runs once per test session. It assumes Alembic is configured
    (e.g., via alembic.ini or environment variables) to point to the
    correct test/development database.
    """
    print("\nApplying Alembic migrations to test database...")
    alembic_config = "alembic.ini" # Assuming alembic.ini is in the root
    if not os.path.exists(alembic_config):
        pytest.fail(f"Alembic config file not found: {alembic_config}")
        
    # Use subprocess to run alembic command
    # Consider error handling more robustly if needed
    try:
        # Make sure DATABASE_URL env var is set if alembic.ini relies on it
        # url = os.getenv("DATABASE_URL", "<default_from_config_if_needed>")
        # print(f"Using database URL for Alembic: {url}") 
        result = subprocess.run(["alembic", "-c", alembic_config, "upgrade", "head"], check=True, capture_output=True, text=True)
        print("Alembic upgrade head completed successfully.")
        print(result.stdout)
    except FileNotFoundError:
        pytest.fail("'alembic' command not found. Is Alembic installed and in the PATH?")
    except subprocess.CalledProcessError as e:
        print(f"Alembic upgrade failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        pytest.fail(f"Alembic upgrade head failed: {e.stderr}")
        
    yield
    # No downgrade by default to preserve schema, assuming transactional tests
    # If needed, add downgrade logic here or manage DB state externally
    # print("\nDowngrading test database schema...")
    # subprocess.run(["alembic", "-c", alembic_config, "downgrade", "base"], check=True)

# --- Transactional Session Fixture --- 

@pytest.fixture(scope="function")
def db_session(apply_migrations):
    """Provides a transactional SQLAlchemy session for each test function.

    Starts a transaction, yields the session, and rolls back the transaction
    after the test completes, ensuring test isolation.
    Depends on the schema being up-to-date via apply_migrations.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection) # Create session bound to this connection
    
    # Optional: Begin nested transaction if SessionLocal doesn't handle it automatically
    # nested = connection.begin_nested() 
    # @pytest.mark.usefixtures("nested")
    
    print("\n[Fixture] Starting DB transaction for test...")
    yield session

    print("\n[Fixture] Rolling back DB transaction...")
    session.close() # Close the session first
    transaction.rollback() # Rollback the transaction
    connection.close() # Close the connection

# --- Test Data Fixtures --- 

@pytest.fixture(scope="function")
def create_test_device(db_session: Session):
    """Fixture factory to create a test device within the test transaction."""
    created_devices = []

    def _create_device(**kwargs):
        default_args = {
            "hostname": f"test-device-{len(created_devices)+1}",
            "ip_address": f"192.168.255.{len(created_devices)+1}",
            "device_type": "pytest_device",
        }
        default_args.update(kwargs) # Override defaults with provided args
        
        device = Device(**default_args)
        db_session.add(device)
        db_session.commit() # Commit within the transaction
        db_session.refresh(device) # Refresh to get ID etc.
        created_devices.append(device)
        print(f"\n[Fixture] Created test device: {device.hostname} (ID: {device.id})")
        return device

    yield _create_device
    
    # Cleanup handled by db_session rollback
    print(f"\n[Fixture] Test device(s) (IDs: {[d.id for d in created_devices]}) rolled back.")

@pytest.fixture(scope="function")
def create_test_job(db_session: Session, create_test_device):
    """Fixture factory to create a test job (linked to a test device)."""
    created_jobs = []

    def _create_job(**kwargs):
        # Create a default device if one isn't provided
        if 'device_id' not in kwargs and 'device' not in kwargs:
            device = create_test_device() # Use the device factory fixture
            kwargs['device_id'] = device.id
        elif 'device' in kwargs:
             device = kwargs.pop('device') # Get device obj if passed directly
             kwargs['device_id'] = device.id
            
        default_args = {
            "status": "pending",
            # Add other required fields if any
        }
        default_args.update(kwargs)
        
        job = Job(**default_args)
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        created_jobs.append(job)
        print(f"\n[Fixture] Created test job (ID: {job.id}) for device ID: {job.device_id}")
        return job

    yield _create_job

    # Cleanup handled by db_session rollback
    print(f"\n[Fixture] Test job(s) (IDs: {[j.id for j in created_jobs]}) rolled back.")
