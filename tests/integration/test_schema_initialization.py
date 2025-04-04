"""
Integration tests for database schema initialization.

This module tests the schema initialization process to ensure it correctly
creates all required tables with the proper structure.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

from netraven.web.database import engine, AsyncSessionLocal, Base
from netraven.web.models import User, Device, Tag, Credential, CredentialTag
from scripts.initialize_schema import initialize_schema

@pytest.fixture
async def db_session():
    """
    Create test session for database operations.
    
    This fixture provides a database session for testing and
    ensures proper cleanup after the test.
    """
    async with AsyncSessionLocal() as session:
        yield session

@pytest.mark.asyncio
async def test_schema_initialization():
    """Test that the schema initialization script works correctly."""
    # Run the initialization script
    try:
        await initialize_schema()
    except Exception as e:
        pytest.fail(f"Schema initialization failed with error: {e}")

    # Verify schema was created correctly
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        
        # Check for required tables
        required_tables = [
            "users", "devices", "tags", "credentials", "credential_tags",
            "backups", "job_logs", "job_log_entries", "scheduled_jobs", 
            "admin_settings", "audit_logs"
        ]
        
        for table in required_tables:
            exists = await conn.run_sync(lambda sync_conn: inspector.has_table(table))
            assert exists, f"Table {table} does not exist"
    
    # Test we can create an object in each essential table
    async with AsyncSessionLocal() as session:
        # Create a test user
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="test_hash"
        )
        session.add(user)
        await session.flush()
        
        # Create a test device
        device = Device(
            hostname="test-device",
            ip_address="192.168.1.1",
            device_type="cisco_ios",
            owner_id=user.id
        )
        session.add(device)
        await session.flush()
        
        # Create a test tag
        tag = Tag(
            name="TestTag",
            description="Test tag"
        )
        session.add(tag)
        await session.flush()
        
        # Create a test credential
        credential = Credential(
            name="TestCredential",
            username="admin",
            password="password123"
        )
        session.add(credential)
        await session.flush()
        
        # Create a credential tag association
        credential_tag = CredentialTag(
            credential_id=credential.id,
            tag_id=tag.id,
            priority=10.0
        )
        session.add(credential_tag)
        await session.flush()
        
        # Test relationships
        device.tags.append(tag)
        await session.flush()
        await session.refresh(device)
        await session.refresh(tag)
        
        assert len(device.tags) == 1
        assert device.tags[0].id == tag.id
        assert len(tag.credential_tags) == 1
        assert tag.credential_tags[0].credential_id == credential.id
        
        # Rollback all changes to leave the database clean
        await session.rollback()

@pytest.mark.asyncio
async def test_database_connection_retry():
    """Test that the database connection retry logic works correctly."""
    # This is a basic test that just ensures the function doesn't raise exceptions
    # In a real environment, we would mock the database connection failures
    from scripts.initialize_schema import wait_for_database
    
    try:
        result = await wait_for_database()
        assert result is True
    except Exception as e:
        pytest.fail(f"Database connection retry failed with error: {e}")

@pytest.mark.asyncio
async def test_schema_validation():
    """Test schema validation after initialization."""
    # Create a session and check key tables
    async with AsyncSessionLocal() as session:
        # Check if we can query tables
        for model_class in [User, Device, Tag, Credential]:
            result = await session.execute(text(f"SELECT COUNT(*) FROM {model_class.__tablename__}"))
            count = result.scalar()
            assert isinstance(count, int), f"Could not query {model_class.__tablename__} table"
        
        # Check foreign key constraints
        # Try to create a credential tag with invalid tag_id
        invalid_credential_tag = CredentialTag(
            credential_id="invalid-credential-id",
            tag_id="invalid-tag-id",
            priority=10.0
        )
        session.add(invalid_credential_tag)
        
        # This should fail due to foreign key constraints
        with pytest.raises(Exception) as excinfo:
            await session.flush()
        
        # Cleanup
        await session.rollback()
    
    # Test passed - schema validation works correctly 