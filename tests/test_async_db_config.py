"""
Test async database configuration.

This module tests the async database configuration and ensures
that the database is properly configured for async operations.
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.web.models.job_log import JobLog
from netraven.web.models.scheduled_job import ScheduledJob


class TestAsyncDatabaseConfiguration:
    """Test class for async database configuration."""

    @pytest.mark.asyncio
    async def test_async_session_creation(self, db_session):
        """Test that async session is created correctly."""
        # Verify that the session is an AsyncSession
        assert isinstance(db_session, AsyncSession)
        
        # Verify that the session is usable
        async with db_session.begin():
            # Try a simple query
            result = await db_session.execute(select(User).limit(1))
            users = result.scalars().all()
            # No assertion on users, just checking that the query executes

    @pytest.mark.asyncio
    async def test_async_transaction_commit(self, db_session, test_user_data):
        """Test that async transactions can be committed."""
        # Create a new user
        user = User(**test_user_data)
        
        # Add and commit in a transaction
        async with db_session.begin():
            db_session.add(user)
        
        # Verify that the user was added
        result = await db_session.execute(
            select(User).where(User.username == test_user_data["username"])
        )
        user = result.scalars().first()
        assert user is not None
        assert user.username == test_user_data["username"]

    @pytest.mark.asyncio
    async def test_async_transaction_rollback(self, db_session, test_user_data):
        """Test that async transactions can be rolled back."""
        # Start a transaction
        async with db_session.begin() as transaction:
            # Create a new user
            user = User(**test_user_data)
            db_session.add(user)
            
            # Roll back the transaction
            await transaction.rollback()
        
        # Verify that the user was not added
        result = await db_session.execute(
            select(User).where(User.username == test_user_data["username"])
        )
        user = result.scalars().first()
        assert user is None

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, db_session, test_user_data, test_device_data):
        """Test that multiple async queries can be executed concurrently."""
        # Create test data
        user = User(**test_user_data)
        device = Device(**test_device_data)
        
        # Add test data
        db_session.add(user)
        db_session.add(device)
        await db_session.commit()
        
        # Define coroutines for concurrent queries
        async def get_user():
            result = await db_session.execute(
                select(User).where(User.username == test_user_data["username"])
            )
            return result.scalars().first()
            
        async def get_device():
            result = await db_session.execute(
                select(Device).where(Device.name == test_device_data["name"])
            )
            return result.scalars().first()
            
        # Execute queries concurrently
        user_result, device_result = await asyncio.gather(get_user(), get_device())
        
        # Verify results
        assert user_result is not None
        assert user_result.username == test_user_data["username"]
        assert device_result is not None
        assert device_result.name == test_device_data["name"]

    @pytest.mark.asyncio
    async def test_connection_pool_behavior(self, test_db):
        """Test connection pool behavior with async operations."""
        # Create multiple sessions
        TestingAsyncSessionLocal, _ = test_db
        sessions = []
        
        # Open 5 sessions
        for _ in range(5):
            session = TestingAsyncSessionLocal()
            sessions.append(session)
            
        # Execute a query in each session
        for session in sessions:
            await session.execute(select(User).limit(1))
            
        # Close all sessions
        for session in sessions:
            await session.close()
            
        # Success if no exceptions were raised

    @pytest.mark.asyncio
    async def test_async_model_relationships(self, db_session, test_backup_device, test_backup):
        """Test that async model relationships work correctly."""
        # Query the device by ID
        result = await db_session.execute(
            select(Device).where(Device.id == test_backup_device.id)
        )
        device = result.scalars().first()
        assert device is not None
        
        # Query the backup with a join to the device
        result = await db_session.execute(
            select(Backup).join(Device).where(Device.id == device.id)
        )
        backup = result.scalars().first()
        assert backup is not None
        assert backup.device_id == device.id 