"""
Unit tests for admin settings functionality.

This module tests the admin settings functionality, including:
- User management
- Role management
- Permission management
- System settings
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy import select

from netraven.web.models.user import User
from netraven.web.models.role import Role
from netraven.web.models.permission import Permission
from netraven.web.models.system_settings import SystemSettings
from netraven.web.auth import UserPrincipal
from netraven.web.auth.jwt import create_access_token
from netraven.web.routers.admin import (
    get_users,
    get_user,
    create_user,
    update_user,
    delete_user,
    get_roles,
    get_role,
    create_role,
    update_role,
    delete_role,
    get_permissions,
    get_permission,
    create_permission,
    update_permission,
    delete_permission,
    get_system_settings,
    update_system_settings
)

# User Management Tests
@pytest.mark.asyncio
async def test_get_users(db_session, test_user, test_admin):
    """Test getting all users."""
    # Create test users
    users = [test_user, test_admin]
    
    # Get users
    result = await get_users(db_session)
    
    # Verify results
    assert len(result) == len(users)
    assert all(user.id in [u.id for u in users] for user in result)

@pytest.mark.asyncio
async def test_get_user(db_session, test_user):
    """Test getting a single user."""
    # Get user
    result = await get_user(test_user.id, db_session)
    
    # Verify result
    assert result.id == test_user.id
    assert result.username == test_user.username
    assert result.email == test_user.email

@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    """Test getting a non-existent user."""
    # Try to get non-existent user
    with pytest.raises(HTTPException) as exc_info:
        await get_user("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_create_user(db_session, test_user_data):
    """Test creating a new user."""
    # Create user
    result = await create_user(test_user_data, db_session)
    
    # Verify result
    assert result.username == test_user_data["username"]
    assert result.email == test_user_data["email"]
    assert result.full_name == test_user_data["full_name"]
    assert result.is_active == test_user_data["is_active"]
    assert result.is_admin == test_user_data["is_admin"]
    
    # Verify user was created in database
    query = select(User).filter(User.id == result.id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.username == test_user_data["username"]

@pytest.mark.asyncio
async def test_create_user_duplicate_username(db_session, test_user):
    """Test creating a user with a duplicate username."""
    # Try to create user with duplicate username
    user_data = {
        "username": test_user.username,
        "email": "different@example.com",
        "full_name": "Different User",
        "password": "password",
        "is_active": True,
        "is_admin": False
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await create_user(user_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 400
    assert "Username already exists" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_update_user(db_session, test_user):
    """Test updating a user."""
    # Update user
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    
    result = await update_user(test_user.id, update_data, db_session)
    
    # Verify result
    assert result.id == test_user.id
    assert result.full_name == update_data["full_name"]
    assert result.email == update_data["email"]
    
    # Verify user was updated in database
    query = select(User).filter(User.id == test_user.id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == update_data["full_name"]
    assert user.email == update_data["email"]

@pytest.mark.asyncio
async def test_update_user_not_found(db_session):
    """Test updating a non-existent user."""
    # Try to update non-existent user
    update_data = {
        "full_name": "Updated Name",
        "email": "updated@example.com"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await update_user("non-existent-id", update_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_delete_user(db_session, test_user):
    """Test deleting a user."""
    # Delete user
    await delete_user(test_user.id, db_session)
    
    # Verify user was deleted from database
    query = select(User).filter(User.id == test_user.id)
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    assert user is None

@pytest.mark.asyncio
async def test_delete_user_not_found(db_session):
    """Test deleting a non-existent user."""
    # Try to delete non-existent user
    with pytest.raises(HTTPException) as exc_info:
        await delete_user("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "User not found" in str(exc_info.value.detail)

# Role Management Tests
@pytest.mark.asyncio
async def test_get_roles(db_session, test_role, test_admin_role):
    """Test getting all roles."""
    # Create test roles
    roles = [test_role, test_admin_role]
    
    # Get roles
    result = await get_roles(db_session)
    
    # Verify results
    assert len(result) == len(roles)
    assert all(role.id in [r.id for r in roles] for role in result)

@pytest.mark.asyncio
async def test_get_role(db_session, test_role):
    """Test getting a single role."""
    # Get role
    result = await get_role(test_role.id, db_session)
    
    # Verify result
    assert result.id == test_role.id
    assert result.name == test_role.name
    assert result.description == test_role.description

@pytest.mark.asyncio
async def test_get_role_not_found(db_session):
    """Test getting a non-existent role."""
    # Try to get non-existent role
    with pytest.raises(HTTPException) as exc_info:
        await get_role("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Role not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_create_role(db_session, test_role_data):
    """Test creating a new role."""
    # Create role
    result = await create_role(test_role_data, db_session)
    
    # Verify result
    assert result.name == test_role_data["name"]
    assert result.description == test_role_data["description"]
    
    # Verify role was created in database
    query = select(Role).filter(Role.id == result.id)
    result = await db_session.execute(query)
    role = result.scalar_one_or_none()
    assert role is not None
    assert role.name == test_role_data["name"]

@pytest.mark.asyncio
async def test_create_role_duplicate_name(db_session, test_role):
    """Test creating a role with a duplicate name."""
    # Try to create role with duplicate name
    role_data = {
        "name": test_role.name,
        "description": "Different description"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await create_role(role_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 400
    assert "Role name already exists" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_update_role(db_session, test_role):
    """Test updating a role."""
    # Update role
    update_data = {
        "name": "Updated Role",
        "description": "Updated description"
    }
    
    result = await update_role(test_role.id, update_data, db_session)
    
    # Verify result
    assert result.id == test_role.id
    assert result.name == update_data["name"]
    assert result.description == update_data["description"]
    
    # Verify role was updated in database
    query = select(Role).filter(Role.id == test_role.id)
    result = await db_session.execute(query)
    role = result.scalar_one_or_none()
    assert role is not None
    assert role.name == update_data["name"]
    assert role.description == update_data["description"]

@pytest.mark.asyncio
async def test_update_role_not_found(db_session):
    """Test updating a non-existent role."""
    # Try to update non-existent role
    update_data = {
        "name": "Updated Role",
        "description": "Updated description"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await update_role("non-existent-id", update_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Role not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_delete_role(db_session, test_role):
    """Test deleting a role."""
    # Delete role
    await delete_role(test_role.id, db_session)
    
    # Verify role was deleted from database
    query = select(Role).filter(Role.id == test_role.id)
    result = await db_session.execute(query)
    role = result.scalar_one_or_none()
    assert role is None

@pytest.mark.asyncio
async def test_delete_role_not_found(db_session):
    """Test deleting a non-existent role."""
    # Try to delete non-existent role
    with pytest.raises(HTTPException) as exc_info:
        await delete_role("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Role not found" in str(exc_info.value.detail)

# Permission Management Tests
@pytest.mark.asyncio
async def test_get_permissions(db_session, test_permission, test_admin_permission):
    """Test getting all permissions."""
    # Create test permissions
    permissions = [test_permission, test_admin_permission]
    
    # Get permissions
    result = await get_permissions(db_session)
    
    # Verify results
    assert len(result) == len(permissions)
    assert all(permission.id in [p.id for p in permissions] for permission in result)

@pytest.mark.asyncio
async def test_get_permission(db_session, test_permission):
    """Test getting a single permission."""
    # Get permission
    result = await get_permission(test_permission.id, db_session)
    
    # Verify result
    assert result.id == test_permission.id
    assert result.name == test_permission.name
    assert result.description == test_permission.description

@pytest.mark.asyncio
async def test_get_permission_not_found(db_session):
    """Test getting a non-existent permission."""
    # Try to get non-existent permission
    with pytest.raises(HTTPException) as exc_info:
        await get_permission("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Permission not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_create_permission(db_session, test_permission_data):
    """Test creating a new permission."""
    # Create permission
    result = await create_permission(test_permission_data, db_session)
    
    # Verify result
    assert result.name == test_permission_data["name"]
    assert result.description == test_permission_data["description"]
    
    # Verify permission was created in database
    query = select(Permission).filter(Permission.id == result.id)
    result = await db_session.execute(query)
    permission = result.scalar_one_or_none()
    assert permission is not None
    assert permission.name == test_permission_data["name"]

@pytest.mark.asyncio
async def test_create_permission_duplicate_name(db_session, test_permission):
    """Test creating a permission with a duplicate name."""
    # Try to create permission with duplicate name
    permission_data = {
        "name": test_permission.name,
        "description": "Different description"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await create_permission(permission_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 400
    assert "Permission name already exists" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_update_permission(db_session, test_permission):
    """Test updating a permission."""
    # Update permission
    update_data = {
        "name": "Updated Permission",
        "description": "Updated description"
    }
    
    result = await update_permission(test_permission.id, update_data, db_session)
    
    # Verify result
    assert result.id == test_permission.id
    assert result.name == update_data["name"]
    assert result.description == update_data["description"]
    
    # Verify permission was updated in database
    query = select(Permission).filter(Permission.id == test_permission.id)
    result = await db_session.execute(query)
    permission = result.scalar_one_or_none()
    assert permission is not None
    assert permission.name == update_data["name"]
    assert permission.description == update_data["description"]

@pytest.mark.asyncio
async def test_update_permission_not_found(db_session):
    """Test updating a non-existent permission."""
    # Try to update non-existent permission
    update_data = {
        "name": "Updated Permission",
        "description": "Updated description"
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await update_permission("non-existent-id", update_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Permission not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_delete_permission(db_session, test_permission):
    """Test deleting a permission."""
    # Delete permission
    await delete_permission(test_permission.id, db_session)
    
    # Verify permission was deleted from database
    query = select(Permission).filter(Permission.id == test_permission.id)
    result = await db_session.execute(query)
    permission = result.scalar_one_or_none()
    assert permission is None

@pytest.mark.asyncio
async def test_delete_permission_not_found(db_session):
    """Test deleting a non-existent permission."""
    # Try to delete non-existent permission
    with pytest.raises(HTTPException) as exc_info:
        await delete_permission("non-existent-id", db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "Permission not found" in str(exc_info.value.detail)

# System Settings Tests
@pytest.mark.asyncio
async def test_get_system_settings(db_session, test_system_settings):
    """Test getting system settings."""
    # Get system settings
    result = await get_system_settings(db_session)
    
    # Verify result
    assert result.id == test_system_settings.id
    assert result.maintenance_mode == test_system_settings.maintenance_mode
    assert result.backup_retention_days == test_system_settings.backup_retention_days
    assert result.max_concurrent_jobs == test_system_settings.max_concurrent_jobs

@pytest.mark.asyncio
async def test_update_system_settings(db_session, test_system_settings):
    """Test updating system settings."""
    # Update system settings
    update_data = {
        "maintenance_mode": True,
        "backup_retention_days": 30,
        "max_concurrent_jobs": 5
    }
    
    result = await update_system_settings(test_system_settings.id, update_data, db_session)
    
    # Verify result
    assert result.id == test_system_settings.id
    assert result.maintenance_mode == update_data["maintenance_mode"]
    assert result.backup_retention_days == update_data["backup_retention_days"]
    assert result.max_concurrent_jobs == update_data["max_concurrent_jobs"]
    
    # Verify system settings were updated in database
    query = select(SystemSettings).filter(SystemSettings.id == test_system_settings.id)
    result = await db_session.execute(query)
    settings = result.scalar_one_or_none()
    assert settings is not None
    assert settings.maintenance_mode == update_data["maintenance_mode"]
    assert settings.backup_retention_days == update_data["backup_retention_days"]
    assert settings.max_concurrent_jobs == update_data["max_concurrent_jobs"]

@pytest.mark.asyncio
async def test_update_system_settings_not_found(db_session):
    """Test updating non-existent system settings."""
    # Try to update non-existent system settings
    update_data = {
        "maintenance_mode": True,
        "backup_retention_days": 30,
        "max_concurrent_jobs": 5
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await update_system_settings("non-existent-id", update_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 404
    assert "System settings not found" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_update_system_settings_invalid_values(db_session, test_system_settings):
    """Test updating system settings with invalid values."""
    # Try to update system settings with invalid values
    update_data = {
        "maintenance_mode": True,
        "backup_retention_days": -1,  # Invalid: negative days
        "max_concurrent_jobs": 0  # Invalid: zero jobs
    }
    
    with pytest.raises(HTTPException) as exc_info:
        await update_system_settings(test_system_settings.id, update_data, db_session)
    
    # Verify error
    assert exc_info.value.status_code == 400
    assert "Invalid values for system settings" in str(exc_info.value.detail)

# Test cases will be added here 