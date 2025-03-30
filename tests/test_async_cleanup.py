import pytest
import asyncio
from sqlalchemy import select, delete, update, text
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.models.user import User
from netraven.web.models.device import Device


class TestAsyncCleanupMechanisms:
    """Test class for asynchronous database cleanup mechanisms."""

    @pytest.mark.asyncio
    async def test_cleanup_after_test(self, db_session, test_user_data):
        """Test that data is properly cleaned up after a test."""
        # Add a user
        user = User(**test_user_data)
        db_session.add(user)
        await db_session.commit()
        
        # Verify user was added
        query = text("SELECT COUNT(*) FROM users")
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 1
        
        # The cleanup fixture should automatically clean up this data after the test

    @pytest.mark.asyncio
    async def test_user_count_is_zero(self, db_session):
        """Test that the user count is zero at the start of this test."""
        # This should be a fresh database with no users
        query = text("SELECT COUNT(*) FROM users")
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 0, f"Expected user count to be 0, but got {count}"

    @pytest.mark.asyncio
    async def test_explicit_cleanup(self, db_session, test_user_data):
        """Test explicit cleanup within a test."""
        # Add a user
        user = User(**test_user_data)
        db_session.add(user)
        await db_session.commit()
        
        # Verify user was added
        query = text("SELECT COUNT(*) FROM users")
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 1
        
        # Explicitly delete the user
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()
        
        # Verify user was deleted
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_with_relationships(self, db_session, test_user_data, test_device_data):
        """Test cleanup with relationships."""
        # Add a user
        user = User(**test_user_data)
        db_session.add(user)
        await db_session.commit()
        
        # Add a device owned by the user
        device_data = test_device_data.copy()
        device_data["owner_id"] = user.id
        device = Device(**device_data)
        db_session.add(device)
        await db_session.commit()
        
        # Verify user and device were added
        user_query = text("SELECT COUNT(*) FROM users")
        device_query = text("SELECT COUNT(*) FROM devices")
        
        result = await db_session.execute(user_query)
        user_count = result.scalar()
        assert user_count == 1
        
        result = await db_session.execute(device_query)
        device_count = result.scalar()
        assert device_count == 1
        
        # The cleanup fixture should automatically clean up this data after the test

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, db_session, test_user_data, test_db):
        """Test that transactions are properly isolated."""
        # Create data in a transaction
        async with db_session.begin():
            user = User(**test_user_data)
            db_session.add(user)
        
        # Verify user was added
        query = text("SELECT COUNT(*) FROM users")
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 1
        
        # Start a new session and transaction
        TestingAsyncSessionLocal, _ = test_db
        async with TestingAsyncSessionLocal() as session2:
            # Roll back the transaction
            async with session2.begin():
                await session2.execute(text("DELETE FROM users"))
                # This will be rolled back
                raise Exception("Intentional exception to trigger rollback")
        
        # Verify the user still exists
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 1  # Should still be 1, not 0

    @pytest.mark.asyncio
    async def test_bulk_cleanup(self, db_session, test_user_data):
        """Test bulk cleanup operations."""
        # Add multiple users
        for i in range(5):
            modified_data = test_user_data.copy()
            modified_data["username"] = f"testuser{i}"
            modified_data["email"] = f"user{i}@example.com"
            user = User(**modified_data)
            db_session.add(user)
        
        await db_session.commit()
        
        # Verify users were added
        query = text("SELECT COUNT(*) FROM users")
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 5
        
        # Perform bulk delete
        await db_session.execute(text("DELETE FROM users"))
        await db_session.commit()
        
        # Verify all users were deleted
        result = await db_session.execute(query)
        count = result.scalar()
        assert count == 0 