"""
User CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting user records. Includes both synchronous and asynchronous implementations.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from netraven.web.models.user import User
from netraven.web.schemas.user import UserCreate, UserUpdate
from netraven.core.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

async def get_user_async(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get a user by ID (async version).
    
    Args:
        db: Async database session
        user_id: ID of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user with id: {user_id} (async)")
    result = await db.execute(
        select(User).filter(User.id == user_id)
    )
    return result.scalars().first()

def get_user(db: Union[Session, AsyncSession], user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        user_id: ID of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user with id: {user_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_user_async(db, user_id)
    else:
        # Synchronous implementation
        return db.query(User).filter(User.id == user_id).first()

async def get_user_by_email_async(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get a user by email address (async version).
    
    Args:
        db: Async database session
        email: Email address to search for
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user by email: {email} (async)")
    result = await db.execute(
        select(User).filter(User.email == email)
    )
    return result.scalars().first()

def get_user_by_email(db: Union[Session, AsyncSession], email: str) -> Optional[User]:
    """
    Get a user by email address.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        email: Email address to search for
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user by email: {email}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_user_by_email_async(db, email)
    else:
        # Synchronous implementation
        return db.query(User).filter(User.email == email).first()

async def get_user_by_username_async(db: AsyncSession, username: str) -> Optional[User]:
    """
    Get a user by username (async version).
    
    Args:
        db: Async database session
        username: Username to search for
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user by username: {username} (async)")
    result = await db.execute(
        select(User).filter(User.username == username)
    )
    return result.scalars().first()

def get_user_by_username(db: Union[Session, AsyncSession], username: str) -> Optional[User]:
    """
    Get a user by username.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        username: Username to search for
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user by username: {username}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_user_by_username_async(db, username)
    else:
        # Synchronous implementation
        return db.query(User).filter(User.username == username).first()

async def get_users_async(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users with pagination (async version).
    
    Args:
        db: Async database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of User objects
    """
    logger.debug(f"Getting users with skip={skip}, limit={limit} (async)")
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    return result.scalars().all()

def get_users(db: Union[Session, AsyncSession], skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users with pagination.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of User objects
    """
    logger.debug(f"Getting users with skip={skip}, limit={limit}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return get_users_async(db, skip, limit)
    else:
        # Synchronous implementation
        return db.query(User).offset(skip).limit(limit).all()

async def create_user_async(db: AsyncSession, user: UserCreate) -> User:
    """
    Create a new user (async version).
    
    Args:
        db: Async database session
        user: User creation data (Pydantic model)
        
    Returns:
        Created User object
    """
    logger.info(f"Creating new user with username: {user.username} (async)")
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create new user
    db_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User created successfully: {db_user.id} (async)")
        return db_user
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError creating user: {str(e)} (async)")
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error creating user: {str(e)} (async)")
        raise

def create_user(db: Union[Session, AsyncSession], user: UserCreate) -> User:
    """
    Create a new user.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        user: User creation data (Pydantic model)
        
    Returns:
        Created User object
    """
    logger.info(f"Creating new user with username: {user.username}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return create_user_async(db, user)
    else:
        # Synchronous implementation
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        # Create new user
        db_user = User(
            id=str(uuid.uuid4()),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=datetime.utcnow()
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            logger.info(f"User created successfully: {db_user.id}")
            return db_user
        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError creating user: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.exception(f"Error creating user: {str(e)}")
            raise

async def update_user_async(db: AsyncSession, user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Update an existing user (async version).
    
    Args:
        db: Async database session
        user_id: ID of the user to update
        user_update: User update data (Pydantic model)
        
    Returns:
        Updated User object, or None if user not found
    """
    logger.info(f"Updating user with id: {user_id} (async)")
    
    # Get existing user
    db_user = await get_user_async(db, user_id)
    if not db_user:
        logger.warning(f"User not found: {user_id} (async)")
        return None
    
    # Update fields that are provided
    if user_update.username is not None:
        db_user.username = user_update.username
    
    if user_update.email is not None:
        db_user.email = user_update.email
    
    if user_update.full_name is not None:
        db_user.full_name = user_update.full_name
    
    if user_update.password is not None:
        db_user.hashed_password = get_password_hash(user_update.password)
    
    if user_update.is_active is not None:
        db_user.is_active = user_update.is_active
    
    if user_update.is_admin is not None:
        db_user.is_admin = user_update.is_admin
    
    db_user.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User updated successfully: {user_id} (async)")
        return db_user
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"IntegrityError updating user: {str(e)} (async)")
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating user: {str(e)} (async)")
        raise

def update_user(db: Union[Session, AsyncSession], user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Update an existing user.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        user_id: ID of the user to update
        user_update: User update data (Pydantic model)
        
    Returns:
        Updated User object, or None if user not found
    """
    logger.info(f"Updating user with id: {user_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return update_user_async(db, user_id, user_update)
    else:
        # Synchronous implementation
        # Get existing user
        db_user = get_user(db, user_id)
        if not db_user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        # Update fields that are provided
        if user_update.username is not None:
            db_user.username = user_update.username
        
        if user_update.email is not None:
            db_user.email = user_update.email
        
        if user_update.full_name is not None:
            db_user.full_name = user_update.full_name
        
        if user_update.password is not None:
            db_user.hashed_password = get_password_hash(user_update.password)
        
        if user_update.is_active is not None:
            db_user.is_active = user_update.is_active
        
        if user_update.is_admin is not None:
            db_user.is_admin = user_update.is_admin
        
        db_user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(db_user)
            logger.info(f"User updated successfully: {user_id}")
            return db_user
        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError updating user: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.exception(f"Error updating user: {str(e)}")
            raise

async def update_user_last_login_async(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Update a user's last login timestamp (async version).
    
    Args:
        db: Async database session
        user_id: ID of the user to update
        
    Returns:
        Updated User object, or None if user not found
    """
    logger.info(f"Updating last login for user: {user_id} (async)")
    
    # Get existing user
    db_user = await get_user_async(db, user_id)
    if not db_user:
        logger.warning(f"User not found: {user_id} (async)")
        return None
    
    # Update last login timestamp
    db_user.last_login = datetime.utcnow()
    db_user.updated_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Last login updated for user: {user_id} (async)")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error updating last login: {str(e)} (async)")
        raise

def update_user_last_login(db: Union[Session, AsyncSession], user_id: str) -> Optional[User]:
    """
    Update a user's last login timestamp.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        user_id: ID of the user to update
        
    Returns:
        Updated User object, or None if user not found
    """
    logger.info(f"Updating last login for user: {user_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return update_user_last_login_async(db, user_id)
    else:
        # Synchronous implementation
        # Get existing user
        db_user = get_user(db, user_id)
        if not db_user:
            logger.warning(f"User not found: {user_id}")
            return None
        
        # Update last login timestamp
        db_user.last_login = datetime.utcnow()
        db_user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(db_user)
            logger.info(f"Last login updated for user: {user_id}")
            return db_user
        except Exception as e:
            db.rollback()
            logger.exception(f"Error updating last login: {str(e)}")
            raise

async def delete_user_async(db: AsyncSession, user_id: str) -> bool:
    """
    Delete a user (async version).
    
    Args:
        db: Async database session
        user_id: ID of the user to delete
        
    Returns:
        True if user was deleted, False if user not found
    """
    logger.info(f"Deleting user: {user_id} (async)")
    
    # Get existing user
    result = await db.execute(select(User).filter(User.id == user_id))
    db_user = result.scalars().first()
    
    if not db_user:
        logger.warning(f"User not found: {user_id} (async)")
        return False
    
    try:
        await db.delete(db_user)
        await db.commit()
        logger.info(f"User deleted: {user_id} (async)")
        return True
    except Exception as e:
        await db.rollback()
        logger.exception(f"Error deleting user: {str(e)} (async)")
        raise

def delete_user(db: Union[Session, AsyncSession], user_id: str) -> bool:
    """
    Delete a user.
    
    This function supports both sync and async database sessions.
    
    Args:
        db: Database session (sync or async)
        user_id: ID of the user to delete
        
    Returns:
        True if user was deleted, False if user not found
    """
    logger.info(f"Deleting user: {user_id}")
    
    if isinstance(db, AsyncSession):
        # Return awaitable coroutine for async usage
        return delete_user_async(db, user_id)
    else:
        # Synchronous implementation
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            logger.warning(f"User not found: {user_id}")
            return False
        
        try:
            db.delete(db_user)
            db.commit()
            logger.info(f"User deleted: {user_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.exception(f"Error deleting user: {str(e)}")
            raise 