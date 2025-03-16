"""
User CRUD operations for the NetRaven web interface.

This module provides database operations for creating, reading, updating, and
deleting user records.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from netraven.web.models.user import User
from netraven.web.schemas.user import UserCreate, UserUpdate
from netraven.web.auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        db: Database session
        user_id: ID of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user with id: {user_id}")
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get a user by email.
    
    Args:
        db: Database session
        email: Email of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user with email: {email}")
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get a user by username.
    
    Args:
        db: Database session
        username: Username of the user to retrieve
        
    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Getting user with username: {username}")
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of User objects
    """
    logger.debug(f"Getting users with skip={skip}, limit={limit}")
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user: User creation data
        
    Returns:
        Created User object
        
    Raises:
        IntegrityError: If a user with the same username or email already exists
    """
    logger.info(f"Creating new user with username: {user.username}")
    
    # Check if user already exists
    db_user = get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"User with username {user.username} already exists")
        raise IntegrityError("User with this username already exists", None, None)
    
    db_user = get_user_by_email(db, user.email)
    if db_user:
        logger.warning(f"User with email {user.email} already exists")
        raise IntegrityError("User with this email already exists", None, None)
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create new user
    db_user = User(
        id=str(uuid.uuid4()),
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User created successfully: {db_user.username}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise

def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
    """
    Update an existing user.
    
    Args:
        db: Database session
        user_id: ID of the user to update
        user_update: User update data
        
    Returns:
        Updated User object if successful, None if user not found
        
    Raises:
        IntegrityError: If update would create a duplicate username or email
    """
    logger.info(f"Updating user with id: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"User with id {user_id} not found")
        return None
    
    # Check if update would create a duplicate username
    if user_update.username and user_update.username != db_user.username:
        existing_username = get_user_by_username(db, user_update.username)
        if existing_username:
            logger.warning(f"Cannot update: username {user_update.username} already exists")
            raise IntegrityError("User with this username already exists", None, None)
    
    # Check if update would create a duplicate email
    if user_update.email and user_update.email != db_user.email:
        existing_email = get_user_by_email(db, user_update.email)
        if existing_email:
            logger.warning(f"Cannot update: email {user_update.email} already exists")
            raise IntegrityError("User with this email already exists", None, None)
    
    # Update user data
    update_data = user_update.model_dump(exclude_unset=True)
    
    # If password is provided, hash it
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    # Update the fields
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    # Always update the updated_at timestamp
    db_user.updated_at = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User updated successfully: {db_user.username}")
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise

def update_user_last_login(db: Session, user_id: str) -> Optional[User]:
    """
    Update a user's last login timestamp.
    
    Args:
        db: Database session
        user_id: ID of the user to update
        
    Returns:
        Updated User object if successful, None if user not found
    """
    logger.debug(f"Updating last login for user with id: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"User with id {user_id} not found")
        return None
    
    db_user.last_login = datetime.utcnow()
    
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user last login: {e}")
        raise

def delete_user(db: Session, user_id: str) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user_id: ID of the user to delete
        
    Returns:
        True if deletion was successful, False if user not found
    """
    logger.info(f"Deleting user with id: {user_id}")
    
    db_user = get_user(db, user_id)
    if not db_user:
        logger.warning(f"User with id {user_id} not found")
        return False
    
    try:
        db.delete(db_user)
        db.commit()
        logger.info(f"User deleted successfully: {db_user.username}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise 