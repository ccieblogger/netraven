"""
Unit tests for device management functionality.

This module tests the device management functionality, including:
- Device CRUD operations
- Device tag operations
- Device backup status tracking
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy import select

from netraven.web.models.device import Device
from netraven.web.models.tag import Tag
from netraven.web.models.user import User
from netraven.web.schemas.device import DeviceCreate, DeviceUpdate
from netraven.web.crud.device import (
    get_devices,
    get_device,
    create_device,
    update_device,
    delete_device,
    update_device_backup_status
)

# Device CRUD Tests
@pytest.mark.asyncio
async def test_get_devices(db_session, test_device):
    """Test getting all devices."""
    # Create test device
    devices = [test_device]
    
    # Get devices
    result = await get_devices(db_session)
    
    # Verify results
    assert len(result) == len(devices)
    assert any(device.id == test_device.id for device in result)

@pytest.mark.asyncio
async def test_get_devices_with_filters(db_session, test_device, test_user):
    """Test getting devices with filters."""
    # Create second device with different device type
    second_device_data = {
        "name": "Test Device 2",
        "hostname": "test2.example.com",
        "ip_address": "192.168.1.2",
        "device_type": "juniper_junos",
        "port": 22,
        "username": "admin",
        "password": "password",
        "enable_password": "enable",
        "tags": ["test", "juniper"],
        "owner_id": test_user.id
    }
    second_device = Device(**second_device_data)
    db_session.add(second_device)
    await db_session.commit()
    
    # Get devices with filter by device type
    result = await get_devices(db_session, device_type="cisco_ios")
    
    # Verify results
    assert len(result) == 1
    assert result[0].id == test_device.id
    
    # Get devices with filter by owner_id
    result = await get_devices(db_session, owner_id=test_user.id)
    
    # Verify results
    assert len(result) == 2  # Both test_device and second_device belong to the user
    
    # Get devices with search by hostname
    result = await get_devices(db_session, search="test2")
    
    # Verify results
    assert len(result) == 1
    assert result[0].id == second_device.id

@pytest.mark.asyncio
async def test_get_device(db_session, test_device):
    """Test getting a single device."""
    # Get device
    result = await get_device(db_session, test_device.id)
    
    # Verify result
    assert result.id == test_device.id
    assert result.hostname == test_device.hostname
    assert result.ip_address == test_device.ip_address
    assert result.device_type == test_device.device_type

@pytest.mark.asyncio
async def test_get_device_not_found(db_session):
    """Test getting a non-existent device."""
    # Try to get non-existent device
    result = await get_device(db_session, "non-existent-id")
    
    # Verify result
    assert result is None

@pytest.mark.asyncio
async def test_create_device(db_session, test_user, test_device_data):
    """Test creating a new device."""
    # Create device create schema
    device_create = DeviceCreate(
        hostname=test_device_data["hostname"],
        ip_address=test_device_data["ip_address"],
        device_type=test_device_data["device_type"],
        port=test_device_data["port"],
        username=test_device_data["username"],
        password=test_device_data["password"],
        description="Test device description"
    )
    
    # Create device
    result = await create_device(db_session, device_create, test_user.id)
    
    # Verify result
    assert result.hostname == device_create.hostname
    assert result.ip_address == device_create.ip_address
    assert result.device_type == device_create.device_type
    assert result.port == device_create.port
    assert result.username == device_create.username
    assert result.description == device_create.description
    assert result.owner_id == test_user.id
    
    # Verify device was created in database
    query = select(Device).filter(Device.id == result.id)
    result_query = await db_session.execute(query)
    device = result_query.scalar_one_or_none()
    assert device is not None
    assert device.hostname == device_create.hostname

@pytest.mark.asyncio
async def test_update_device(db_session, test_device):
    """Test updating a device."""
    # Update device
    update_data = DeviceUpdate(
        hostname="updated.example.com",
        description="Updated description"
    )
    
    result = await update_device(db_session, test_device.id, update_data)
    
    # Verify result
    assert result.id == test_device.id
    assert result.hostname == update_data.hostname
    assert result.description == update_data.description
    
    # Verify device was updated in database
    query = select(Device).filter(Device.id == test_device.id)
    result_query = await db_session.execute(query)
    device = result_query.scalar_one_or_none()
    assert device is not None
    assert device.hostname == update_data.hostname
    assert device.description == update_data.description

@pytest.mark.asyncio
async def test_update_device_not_found(db_session):
    """Test updating a non-existent device."""
    # Try to update non-existent device
    update_data = DeviceUpdate(
        hostname="updated.example.com",
        description="Updated description"
    )
    
    result = await update_device(db_session, "non-existent-id", update_data)
    
    # Verify result
    assert result is None

@pytest.mark.asyncio
async def test_delete_device(db_session, test_device):
    """Test deleting a device."""
    # Delete device
    result = await delete_device(db_session, test_device.id)
    
    # Verify result
    assert result is True
    
    # Verify device was deleted from database
    query = select(Device).filter(Device.id == test_device.id)
    result_query = await db_session.execute(query)
    device = result_query.scalar_one_or_none()
    assert device is None

@pytest.mark.asyncio
async def test_delete_device_not_found(db_session):
    """Test deleting a non-existent device."""
    # Try to delete non-existent device
    result = await delete_device(db_session, "non-existent-id")
    
    # Verify result
    assert result is False

@pytest.mark.asyncio
async def test_update_device_backup_status(db_session, test_device):
    """Test updating device backup status."""
    # Update backup status
    status = "success"
    timestamp = datetime.utcnow()
    
    result = await update_device_backup_status(db_session, test_device.id, status, timestamp)
    
    # Verify result
    assert result.id == test_device.id
    assert result.last_backup_status == status
    assert result.last_backup_at == timestamp
    
    # Verify device was updated in database
    query = select(Device).filter(Device.id == test_device.id)
    result_query = await db_session.execute(query)
    device = result_query.scalar_one_or_none()
    assert device is not None
    assert device.last_backup_status == status
    assert device.last_backup_at == timestamp

@pytest.mark.asyncio
async def test_update_device_backup_status_not_found(db_session):
    """Test updating backup status for a non-existent device."""
    # Try to update backup status for non-existent device
    status = "success"
    timestamp = datetime.utcnow()
    
    result = await update_device_backup_status(db_session, "non-existent-id", status, timestamp)
    
    # Verify result
    assert result is None

# Device Tag Tests
@pytest.mark.asyncio
async def test_get_tags_for_device(db_session, test_device, test_tag):
    """Test getting tags for a device."""
    # Associate tag with device
    from netraven.web.crud.tag import add_tag_to_device
    await add_tag_to_device(db_session, test_device.id, test_tag.id)
    
    # Get tags for device
    from netraven.web.crud.tag import get_tags_for_device
    result = await get_tags_for_device(db_session, test_device.id)
    
    # Verify results
    assert len(result) == 1
    assert result[0].id == test_tag.id

@pytest.mark.asyncio
async def test_get_devices_for_tag(db_session, test_device, test_tag):
    """Test getting devices for a tag."""
    # Associate tag with device
    from netraven.web.crud.tag import add_tag_to_device
    await add_tag_to_device(db_session, test_device.id, test_tag.id)
    
    # Get devices for tag
    from netraven.web.crud.tag import get_devices_for_tag
    result = await get_devices_for_tag(db_session, test_tag.id)
    
    # Verify results
    assert len(result) == 1
    assert result[0].id == test_device.id

@pytest.mark.asyncio
async def test_add_tag_to_device(db_session, test_device, test_tag):
    """Test adding a tag to a device."""
    # Add tag to device
    from netraven.web.crud.tag import add_tag_to_device
    await add_tag_to_device(db_session, test_device.id, test_tag.id)
    
    # Verify tag was added
    from netraven.web.crud.tag import get_tags_for_device
    tags = await get_tags_for_device(db_session, test_device.id)
    assert len(tags) == 1
    assert tags[0].id == test_tag.id

@pytest.mark.asyncio
async def test_remove_tag_from_device(db_session, test_device, test_tag):
    """Test removing a tag from a device."""
    # Add tag to device
    from netraven.web.crud.tag import add_tag_to_device
    await add_tag_to_device(db_session, test_device.id, test_tag.id)
    
    # Remove tag from device
    from netraven.web.crud.tag import remove_tag_from_device
    await remove_tag_from_device(db_session, test_device.id, test_tag.id)
    
    # Verify tag was removed
    from netraven.web.crud.tag import get_tags_for_device
    tags = await get_tags_for_device(db_session, test_device.id)
    assert len(tags) == 0

@pytest.mark.asyncio
async def test_bulk_add_tags_to_devices(db_session, test_device, test_tag, test_user):
    """Test bulk adding tags to devices."""
    # Create a second device and tag
    second_device_data = {
        "name": "Test Device 2",
        "hostname": "test2.example.com",
        "ip_address": "192.168.1.2",
        "device_type": "juniper_junos",
        "port": 22,
        "username": "admin",
        "password": "password",
        "owner_id": test_user.id
    }
    second_device = Device(**second_device_data)
    db_session.add(second_device)
    
    second_tag_data = {
        "name": "Test Tag 2",
        "description": "Second test tag",
        "color": "#00FF00"
    }
    second_tag = Tag(**second_tag_data)
    db_session.add(second_tag)
    await db_session.commit()
    
    # Bulk add tags to devices
    from netraven.web.crud.tag import bulk_add_tags_to_devices
    device_ids = [test_device.id, second_device.id]
    tag_ids = [test_tag.id, second_tag.id]
    await bulk_add_tags_to_devices(db_session, device_ids, tag_ids)
    
    # Verify tags were added to first device
    from netraven.web.crud.tag import get_tags_for_device
    tags1 = await get_tags_for_device(db_session, test_device.id)
    assert len(tags1) == 2
    tag_ids1 = [tag.id for tag in tags1]
    assert test_tag.id in tag_ids1
    assert second_tag.id in tag_ids1
    
    # Verify tags were added to second device
    tags2 = await get_tags_for_device(db_session, second_device.id)
    assert len(tags2) == 2
    tag_ids2 = [tag.id for tag in tags2]
    assert test_tag.id in tag_ids2
    assert second_tag.id in tag_ids2

@pytest.mark.asyncio
async def test_bulk_remove_tags_from_devices(db_session, test_device, test_tag, test_user):
    """Test bulk removing tags from devices."""
    # Create a second device and tag
    second_device_data = {
        "name": "Test Device 2",
        "hostname": "test2.example.com",
        "ip_address": "192.168.1.2",
        "device_type": "juniper_junos",
        "port": 22,
        "username": "admin",
        "password": "password",
        "owner_id": test_user.id
    }
    second_device = Device(**second_device_data)
    db_session.add(second_device)
    
    second_tag_data = {
        "name": "Test Tag 2",
        "description": "Second test tag",
        "color": "#00FF00"
    }
    second_tag = Tag(**second_tag_data)
    db_session.add(second_tag)
    await db_session.commit()
    
    # Add tags to devices
    from netraven.web.crud.tag import bulk_add_tags_to_devices
    device_ids = [test_device.id, second_device.id]
    tag_ids = [test_tag.id, second_tag.id]
    await bulk_add_tags_to_devices(db_session, device_ids, tag_ids)
    
    # Bulk remove one tag from devices
    from netraven.web.crud.tag import bulk_remove_tags_from_devices
    await bulk_remove_tags_from_devices(db_session, device_ids, [test_tag.id])
    
    # Verify first tag was removed from both devices
    from netraven.web.crud.tag import get_tags_for_device
    tags1 = await get_tags_for_device(db_session, test_device.id)
    assert len(tags1) == 1
    assert tags1[0].id == second_tag.id
    
    tags2 = await get_tags_for_device(db_session, second_device.id)
    assert len(tags2) == 1
    assert tags2[0].id == second_tag.id 