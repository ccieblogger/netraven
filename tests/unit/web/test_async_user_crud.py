"""
Unit tests for async user CRUD operations.

This module contains tests for the async user CRUD operations in the web interface.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from netraven.web.crud.user import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    get_users,
    create_user,
    update_user,
    update_user_last_login,
    delete_user
)
from netraven.web.models.user import User
from netraven.web.schemas.user import UserCreate, UserUpdate


@pytest.fixture
async def test_user_data():
    """Return test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "password123",
        "is_active": True,
        "is_admin": False
    }


@pytest.fixture
async def test_user(db_session, test_user_data):
    """Create a test user for use in tests."""
    user_data = UserCreate(**test_user_data)
    user = await create_user(db_session, user_data)
    return user


@pytest.mark.asyncio
async def test_get_user_async(db_session: AsyncSession, test_user):
    """Test getting a user by ID using async session."""
    # Act
    result = await get_user(db_session, test_user.id)
    
    # Assert
    assert result is not None
    assert result.id == test_user.id
    assert result.username == test_user.username
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_not_found_async(db_session: AsyncSession):
    """Test getting a non-existent user by ID using async session."""
    # Act
    result = await get_user(db_session, "non-existent-id")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_email_async(db_session: AsyncSession, test_user):
    """Test getting a user by email using async session."""
    # Act
    result = await get_user_by_email(db_session, test_user.email)
    
    # Assert
    assert result is not None
    assert result.id == test_user.id
    assert result.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_email_not_found_async(db_session: AsyncSession):
    """Test getting a non-existent user by email using async session."""
    # Act
    result = await get_user_by_email(db_session, "nonexistent@example.com")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_user_by_username_async(db_session: AsyncSession, test_user):
    """Test getting a user by username using async session."""
    # Act
    result = await get_user_by_username(db_session, test_user.username)
    
    # Assert
    assert result is not None
    assert result.id == test_user.id
    assert result.username == test_user.username


@pytest.mark.asyncio
async def test_get_user_by_username_not_found_async(db_session: AsyncSession):
    """Test getting a non-existent user by username using async session."""
    # Act
    result = await get_user_by_username(db_session, "nonexistentuser")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_users_async(db_session: AsyncSession, test_user):
    """Test getting a list of users using async session."""
    # Create another test user
    user_data = UserCreate(
        username="anotheruser",
        email="another@example.com",
        full_name="Another User",
        password="password123",
        is_active=True,
        is_admin=False
    )
    await create_user(db_session, user_data)
    
    # Act
    users = await get_users(db_session)
    
    # Assert
    assert len(users) == 2
    assert any(u.username == "testuser" for u in users)
    assert any(u.username == "anotheruser" for u in users)


@pytest.mark.asyncio
async def test_create_user_async(db_session: AsyncSession):
    """Test creating a user using async session."""
    # Arrange
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        full_name="New User",
        password="password123",
        is_active=True,
        is_admin=False
    )
    
    # Act
    user = await create_user(db_session, user_data)
    
    # Assert
    assert user is not None
    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "new@example.com"
    assert user.full_name == "New User"
    assert user.is_active is True
    assert user.is_admin is False
    
    # Verify it was actually saved to the database
    result = await get_user(db_session, user.id)
    assert result is not None
    assert result.username == "newuser"


@pytest.mark.asyncio
async def test_update_user_async(db_session: AsyncSession, test_user):
    """Test updating a user using async session."""
    # Arrange
    user_update = UserUpdate(
        username="updateduser",
        email="updated@example.com",
        full_name="Updated User"
    )
    
    # Act
    updated_user = await update_user(db_session, test_user.id, user_update)
    
    # Assert
    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.username == "updateduser"
    assert updated_user.email == "updated@example.com"
    assert updated_user.full_name == "Updated User"
    
    # Verify it was actually updated in the database
    result = await get_user(db_session, test_user.id)
    assert result.username == "updateduser"


@pytest.mark.asyncio
async def test_update_user_not_found_async(db_session: AsyncSession):
    """Test updating a non-existent user using async session."""
    # Arrange
    user_update = UserUpdate(username="updateduser")
    
    # Act
    result = await update_user(db_session, "non-existent-id", user_update)
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_update_user_last_login_async(db_session: AsyncSession, test_user):
    """Test updating a user's last login timestamp using async session."""
    # Record time before update
    before_update = datetime.utcnow() - timedelta(seconds=1)
    
    # Act
    updated_user = await update_user_last_login(db_session, test_user.id)
    
    # Assert
    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.last_login is not None
    assert updated_user.last_login > before_update
    
    # Verify it was actually updated in the database
    result = await get_user(db_session, test_user.id)
    assert result.last_login is not None
    assert result.last_login > before_update


@pytest.mark.asyncio
async def test_update_user_last_login_not_found_async(db_session: AsyncSession):
    """Test updating a non-existent user's last login timestamp using async session."""
    # Act
    result = await update_user_last_login(db_session, "non-existent-id")
    
    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_delete_user_async(db_session: AsyncSession, test_user):
    """Test deleting a user using async session."""
    # Act
    result = await delete_user(db_session, test_user.id)
    
    # Assert
    assert result is True
    
    # Verify it was actually deleted from the database
    deleted_user = await get_user(db_session, test_user.id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_delete_user_not_found_async(db_session: AsyncSession):
    """Test deleting a non-existent user using async session."""
    # Act
    result = await delete_user(db_session, "non-existent-id")
    
    # Assert
    assert result is False 