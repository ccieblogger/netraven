"""
Unit tests for async backup CRUD operations.

This module contains tests for the async backup CRUD operations in the web interface.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.crud.backup import (
    get_backup,
    get_backups,
    create_backup,
    delete_backup,
    get_backup_content
)
from netraven.web.models.backup import Backup
from netraven.web.schemas.backup import BackupCreate


@pytest.fixture
async def test_device_id():
    """Return a test device ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def test_backup(db_session, test_device_id):
    """Create a test backup for use in tests."""
    backup_data = BackupCreate(
        device_id=test_device_id,
        config_type="running"
    )
    
    backup = await create_backup(
        db_session, 
        backup_data, 
        serial_number="SN12345",
        content="test backup content"
    )
    return backup


@pytest.mark.asyncio
async def test_get_backup_async(db_session: AsyncSession, test_backup):
    """Test getting a backup by ID using async session."""
    # Act
    result = await get_backup(db_session, test_backup.id)
    
    # Assert
    assert result is not None
    assert result.id == test_backup.id
    assert result.device_id == test_backup.device_id
    assert result.config_type == test_backup.config_type


@pytest.mark.asyncio
async def test_get_backup_not_found_async(db_session: AsyncSession):
    """Test getting a non-existent backup by ID using async session."""
    # Act
    result = await get_backup(db_session, "non-existent-id")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_backups_async(db_session: AsyncSession, test_device_id):
    """Test getting a list of backups using async session."""
    # Create multiple test backups
    for i in range(3):
        backup_data = BackupCreate(
            device_id=test_device_id,
            config_type="running" if i % 2 == 0 else "startup"
        )
        await create_backup(
            db_session, 
            backup_data, 
            serial_number=f"SN{i}",
            content=f"test backup content {i}"
        )
    
    # Act - get all backups
    backups = await get_backups(db_session)
    
    # Assert
    assert len(backups) == 3
    
    # Act - filter by device_id
    backups = await get_backups(db_session, device_id=test_device_id)
    
    # Assert
    assert len(backups) == 3
    
    # Act - filter by config_type
    backups = await get_backups(db_session, config_type="running")
    
    # Assert
    assert len(backups) == 2
    assert all(b.config_type == "running" for b in backups)


@pytest.mark.asyncio
async def test_get_backups_with_date_filter_async(db_session: AsyncSession, test_device_id):
    """Test getting backups with date filters using async session."""
    # Create backups with different dates
    dates = [
        datetime.utcnow() - timedelta(days=5),
        datetime.utcnow() - timedelta(days=3),
        datetime.utcnow() - timedelta(days=1)
    ]
    
    for i, date in enumerate(dates):
        backup_data = BackupCreate(
            device_id=test_device_id,
            config_type="running"
        )
        backup = await create_backup(
            db_session, 
            backup_data, 
            serial_number=f"SN{i}",
            content=f"test backup content {i}"
        )
        
        # Update the created_at date
        backup.created_at = date
        await db_session.commit()
    
    # Act - filter by start_date
    start_date = datetime.utcnow() - timedelta(days=4)
    backups = await get_backups(db_session, start_date=start_date)
    
    # Assert
    assert len(backups) == 2
    
    # Act - filter by end_date
    end_date = datetime.utcnow() - timedelta(days=2)
    backups = await get_backups(db_session, end_date=end_date)
    
    # Assert
    assert len(backups) == 2
    
    # Act - filter by date range
    start_date = datetime.utcnow() - timedelta(days=4)
    end_date = datetime.utcnow() - timedelta(days=2)
    backups = await get_backups(db_session, start_date=start_date, end_date=end_date)
    
    # Assert
    assert len(backups) == 1


@pytest.mark.asyncio
async def test_create_backup_async(db_session: AsyncSession, test_device_id):
    """Test creating a backup using async session."""
    # Arrange
    backup_data = BackupCreate(
        device_id=test_device_id,
        config_type="startup"
    )
    
    # Act
    backup = await create_backup(
        db_session, 
        backup_data, 
        serial_number="SN12345",
        content="test backup content for startup"
    )
    
    # Assert
    assert backup is not None
    assert backup.id is not None
    assert backup.device_id == test_device_id
    assert backup.config_type == "startup"
    assert backup.serial_number == "SN12345"
    
    # Verify it was actually saved to the database
    result = await get_backup(db_session, backup.id)
    assert result is not None
    assert result.device_id == test_device_id


@pytest.mark.asyncio
async def test_delete_backup_async(db_session: AsyncSession, test_backup):
    """Test deleting a backup using async session."""
    # Act
    result = await delete_backup(db_session, test_backup.id)
    
    # Assert
    assert result is True
    
    # Verify it was actually deleted from the database
    deleted_backup = await get_backup(db_session, test_backup.id)
    assert deleted_backup is None


@pytest.mark.asyncio
async def test_delete_backup_not_found_async(db_session: AsyncSession):
    """Test deleting a non-existent backup using async session."""
    # Act
    result = await delete_backup(db_session, "non-existent-id")
    
    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_get_backup_content_async(db_session: AsyncSession, test_backup):
    """Test getting backup content using async session."""
    # Act
    content = await get_backup_content(db_session, test_backup.id)
    
    # Assert
    assert content is not None
    assert content == "test backup content"


@pytest.mark.asyncio
async def test_get_backup_content_not_found_async(db_session: AsyncSession):
    """Test getting content of a non-existent backup using async session."""
    # Act
    content = await get_backup_content(db_session, "non-existent-id")
    
    # Assert
    assert content is None 