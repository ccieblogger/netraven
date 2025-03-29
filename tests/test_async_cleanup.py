"""
Test async cleanup mechanisms.

This module tests the mechanisms for cleaning up test data
after async tests are completed.
"""

import pytest
import asyncio
from sqlalchemy.future import select
from sqlalchemy import delete, func

from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.web.models.job_log import JobLog
from netraven.web.models.scheduled_job import ScheduledJob


class TestAsyncCleanupMechanisms:
    """Test class for async cleanup mechanisms."""

    @pytest.mark.asyncio
    async def test_cleanup_after_test(self, db_session, test_user_data):
        """Test that data is properly cleaned up after a test."""
        # Add a user
        user = User(**test_user_data)
        db_session.add(user)
        await db_session.commit()
        
        # Verify the user was added
        result = await db_session.execute(select(User).where(User.username == test_user_data["username"]))
        user = result.scalars().first()
        assert user is not None
        
        # End of test - cleanup should happen automatically via the cleanup_test_data fixture

    @pytest.mark.asyncio
    async def test_user_count_is_zero(self, db_session):
        """Test that the user count is zero after the previous test."""
        # Query user count
        result = await db_session.execute(select(func.count()).select_from(User))
        count = result.scalar()
        
        # Verify no users exist
        assert count == 0, f"Expected user count to be 0, but got {count}"

    @pytest.mark.asyncio
    async def test_explicit_cleanup(self, db_session, test_device_data):
        """Test explicit cleanup of test data."""
        # Add a device
        device = Device(**test_device_data)
        db_session.add(device)
        await db_session.commit()
        
        # Verify the device was added
        result = await db_session.execute(select(Device).where(Device.name == test_device_data["name"]))
        device = result.scalars().first()
        assert device is not None
        
        # Explicitly clean up
        await db_session.execute(delete(Device).where(Device.name == test_device_data["name"]))
        await db_session.commit()
        
        # Verify the device was deleted
        result = await db_session.execute(select(Device).where(Device.name == test_device_data["name"]))
        device = result.scalars().first()
        assert device is None

    @pytest.mark.asyncio
    async def test_cleanup_with_relationships(self, db_session, test_backup_device, test_backup):
        """Test cleanup of data with relationships."""
        # Verify the backup and device exist
        device_result = await db_session.execute(select(Device).where(Device.id == test_backup_device.id))
        device = device_result.scalars().first()
        assert device is not None
        
        backup_result = await db_session.execute(select(Backup).where(Backup.device_id == test_backup_device.id))
        backup = backup_result.scalars().first()
        assert backup is not None
        
        # Explicitly clean up in correct order (respect foreign key constraints)
        await db_session.execute(delete(Backup).where(Backup.device_id == test_backup_device.id))
        await db_session.commit()
        
        await db_session.execute(delete(Device).where(Device.id == test_backup_device.id))
        await db_session.commit()
        
        # Verify cleanup was successful
        device_result = await db_session.execute(select(Device).where(Device.id == test_backup_device.id))
        device = device_result.scalars().first()
        assert device is None
        
        backup_result = await db_session.execute(select(Backup).where(Backup.id == test_backup.id))
        backup = backup_result.scalars().first()
        assert backup is None

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_session, test_user_data, test_db):
        """Test that transactions are properly isolated."""
        # Create data in a transaction
        async with db_session.begin():
            user = User(**test_user_data)
            db_session.add(user)
        
        # Create a new session
        TestingAsyncSessionLocal, _ = test_db
        async with TestingAsyncSessionLocal() as new_session:
            # Verify data is visible in the new session
            result = await new_session.execute(select(User).where(User.username == test_user_data["username"]))
            user = result.scalars().first()
            assert user is not None
            
            # Clean up in the new session
            await new_session.execute(delete(User).where(User.username == test_user_data["username"]))
            await new_session.commit()
        
        # Verify data is gone in the original session
        result = await db_session.execute(select(User).where(User.username == test_user_data["username"]))
        user = result.scalars().first()
        assert user is None

    @pytest.mark.asyncio
    async def test_bulk_cleanup(self, db_session):
        """Test bulk cleanup of multiple records."""
        # Add multiple users
        users = []
        for i in range(5):
            user = User(
                username=f"testuser{i}",
                email=f"test{i}@example.com",
                full_name=f"Test User {i}",
                password="testpass",
                is_active=True,
                is_admin=False
            )
            users.append(user)
        
        # Add users in bulk
        db_session.add_all(users)
        await db_session.commit()
        
        # Verify users were added
        result = await db_session.execute(select(func.count()).select_from(User))
        count = result.scalar()
        assert count == 5
        
        # Bulk delete
        await db_session.execute(delete(User).where(User.username.like("testuser%")))
        await db_session.commit()
        
        # Verify users were deleted
        result = await db_session.execute(select(func.count()).select_from(User))
        count = result.scalar()
        assert count == 0 