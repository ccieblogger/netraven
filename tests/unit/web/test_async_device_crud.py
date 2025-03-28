"""
Unit tests for async device CRUD operations.

This module contains tests for the async device CRUD operations in the web interface.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.crud.device import (
    get_device,
    get_devices,
    create_device,
    update_device,
    update_device_backup_status,
    delete_device
)
from netraven.web.models.device import Device
from netraven.web.schemas.device import DeviceCreate, DeviceUpdate


@pytest.fixture
async def test_device(db_session):
    """Create a test device for use in tests."""
    device_data = DeviceCreate(
        hostname="test-device.example.com",
        ip_address="192.168.1.100",
        device_type="cisco_ios",
        port=22,
        username="admin",
        password="password123",
        description="Test device for unit tests"
    )
    
    device = await create_device(db_session, device_data, owner_id="test-user")
    return device


@pytest.mark.asyncio
async def test_get_device_async(db_session: AsyncSession, test_device):
    """Test getting a device by ID using async session."""
    # Act
    result = await get_device(db_session, test_device.id)
    
    # Assert
    assert result is not None
    assert result.id == test_device.id
    assert result.hostname == test_device.hostname
    assert result.ip_address == test_device.ip_address


@pytest.mark.asyncio
async def test_get_device_not_found_async(db_session: AsyncSession):
    """Test getting a non-existent device by ID using async session."""
    # Act
    result = await get_device(db_session, "non-existent-id")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_devices_async(db_session: AsyncSession, test_device):
    """Test getting a list of devices using async session."""
    # Create another test device
    device_data = DeviceCreate(
        hostname="another-device.example.com",
        ip_address="192.168.1.101",
        device_type="juniper_junos",
        port=22,
        username="admin",
        password="password123",
        description="Another test device"
    )
    await create_device(db_session, device_data, owner_id="test-user")
    
    # Act
    devices = await get_devices(db_session)
    
    # Assert
    assert len(devices) == 2
    assert any(d.hostname == "test-device.example.com" for d in devices)
    assert any(d.hostname == "another-device.example.com" for d in devices)


@pytest.mark.asyncio
async def test_get_devices_with_filter_async(db_session: AsyncSession, test_device):
    """Test getting a filtered list of devices using async session."""
    # Create another test device
    device_data = DeviceCreate(
        hostname="another-device.example.com",
        ip_address="192.168.1.101",
        device_type="juniper_junos",
        port=22,
        username="admin",
        password="password123",
        description="Another test device"
    )
    await create_device(db_session, device_data, owner_id="test-user")
    
    # Act - filter by device type
    devices = await get_devices(db_session, device_type="cisco_ios")
    
    # Assert
    assert len(devices) == 1
    assert devices[0].hostname == "test-device.example.com"
    
    # Act - filter by search term
    devices = await get_devices(db_session, search="another")
    
    # Assert
    assert len(devices) == 1
    assert devices[0].hostname == "another-device.example.com"


@pytest.mark.asyncio
async def test_create_device_async(db_session: AsyncSession):
    """Test creating a device using async session."""
    # Arrange
    device_data = DeviceCreate(
        hostname="new-device.example.com",
        ip_address="192.168.1.102",
        device_type="arista_eos",
        port=22,
        username="admin",
        password="password123",
        description="New test device"
    )
    
    # Act
    device = await create_device(db_session, device_data, owner_id="test-user")
    
    # Assert
    assert device is not None
    assert device.id is not None
    assert device.hostname == "new-device.example.com"
    assert device.ip_address == "192.168.1.102"
    assert device.device_type == "arista_eos"
    assert device.owner_id == "test-user"
    
    # Verify it was actually saved to the database
    result = await get_device(db_session, device.id)
    assert result is not None
    assert result.hostname == "new-device.example.com"


@pytest.mark.asyncio
async def test_update_device_async(db_session: AsyncSession, test_device):
    """Test updating a device using async session."""
    # Arrange
    device_update = DeviceUpdate(
        hostname="updated-device.example.com",
        ip_address="192.168.1.200",
        description="Updated test device"
    )
    
    # Act
    updated_device = await update_device(db_session, test_device.id, device_update)
    
    # Assert
    assert updated_device is not None
    assert updated_device.id == test_device.id
    assert updated_device.hostname == "updated-device.example.com"
    assert updated_device.ip_address == "192.168.1.200"
    assert updated_device.description == "Updated test device"
    
    # Verify it was actually updated in the database
    result = await get_device(db_session, test_device.id)
    assert result.hostname == "updated-device.example.com"


@pytest.mark.asyncio
async def test_update_device_not_found_async(db_session: AsyncSession):
    """Test updating a non-existent device using async session."""
    # Arrange
    device_update = DeviceUpdate(hostname="updated-device.example.com")
    
    # Act
    result = await update_device(db_session, "non-existent-id", device_update)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_device_backup_status_async(db_session: AsyncSession, test_device):
    """Test updating a device's backup status using async session."""
    # Arrange
    status = "success"
    timestamp = datetime.utcnow()
    
    # Act
    updated_device = await update_device_backup_status(db_session, test_device.id, status, timestamp)
    
    # Assert
    assert updated_device is not None
    assert updated_device.id == test_device.id
    assert updated_device.backup_status == status
    assert updated_device.last_backup == timestamp
    
    # Verify it was actually updated in the database
    result = await get_device(db_session, test_device.id)
    assert result.backup_status == status
    assert result.last_backup == timestamp


@pytest.mark.asyncio
async def test_update_device_backup_status_not_found_async(db_session: AsyncSession):
    """Test updating a non-existent device's backup status using async session."""
    # Act
    result = await update_device_backup_status(db_session, "non-existent-id", "success")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_delete_device_async(db_session: AsyncSession, test_device):
    """Test deleting a device using async session."""
    # Act
    result = await delete_device(db_session, test_device.id)
    
    # Assert
    assert result is True
    
    # Verify it was actually deleted from the database
    deleted_device = await get_device(db_session, test_device.id)
    assert deleted_device is None


@pytest.mark.asyncio
async def test_delete_device_not_found_async(db_session: AsyncSession):
    """Test deleting a non-existent device using async session."""
    # Act
    result = await delete_device(db_session, "non-existent-id")
    
    # Assert
    assert result is False 