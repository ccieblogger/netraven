"""User management router for authentication and access control.

This module provides API endpoints for managing user accounts in the system.
It implements CRUD operations for users with proper security practices
including password hashing and role-based access control.

Most endpoints in this router require administrator privileges, with the
exception of the /me endpoint which allows users to retrieve their own
information. The router handles user creation, retrieval, update, and deletion,
with filtering and pagination capabilities.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from netraven.api import schemas
from netraven.api.dependencies import get_db_session, get_current_active_user, require_admin_role
from netraven.db import models
from netraven.api import auth

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    # Most user routes require admin, apply dependency here or per-route
    dependencies=[Depends(require_admin_role)] 
)

@router.post("/", response_model=schemas.user.User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: schemas.user.UserCreate,
    db: Session = Depends(get_db_session)
):
    """Create a new user account in the system.
    
    Registers a new user with the provided details. The password is hashed
    before storage for security. This endpoint is restricted to administrators.
    
    Args:
        user: User creation schema with username, password, and other details
        db: Database session
        
    Returns:
        The created user object with its assigned ID (password not included)
        
    Raises:
        HTTPException (400): If the username already exists
        HTTPException (403): If the requester lacks admin privileges
    """
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(**user.model_dump(exclude={'password'}), hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Allow user to get their own info without needing admin role
@router.get("/me", response_model=schemas.user.User, tags=["Current User"])
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    """Get the currently authenticated user's profile.
    
    Returns information about the currently logged-in user based on 
    their JWT token. This endpoint is accessible to all authenticated users.
    
    Args:
        current_user: User object injected by the authentication dependency
        
    Returns:
        The current user's profile information
    """
    return current_user

# Admin routes
@router.get("/", response_model=schemas.user.PaginatedUserPublicResponse)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    username: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db_session)
):
    """Retrieve a list of all users with pagination and filtering.
    
    Returns a paginated list of users with optional filtering by username,
    role, and active status. This endpoint is restricted to administrators.
    
    Args:
        page: Page number (starts at 1)
        size: Number of items per page (1-100)
        username: Optional filter by username (partial match)
        role: Optional filter by role (e.g., "admin", "user")
        is_active: Optional filter by account active status
        db: Database session
        
    Returns:
        Paginated response containing user items, total count, and pagination info
        
    Raises:
        HTTPException (403): If the requester lacks admin privileges
    """
    query = db.query(models.User)
    
    # Apply filters
    filters = []
    if username:
        filters.append(models.User.username.ilike(f"%{username}%"))
    if role:
        filters.append(models.User.role == role)
    if is_active is not None:
        filters.append(models.User.is_active == is_active)
    
    # Apply all filters
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count for pagination
    total = query.count()
    
    # Calculate pagination values
    pages = (total + size - 1) // size if total > 0 else 1
    offset = (page - 1) * size
    
    # Get paginated users
    users = query.offset(offset).limit(size).all()
    
    # Return paginated response
    return {
        "items": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }

@router.get("/{user_id}", response_model=schemas.user.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    """Retrieve a specific user by ID.
    
    Fetches detailed information about a single user by their ID.
    This endpoint is restricted to administrators.
    
    Args:
        user_id: ID of the user to retrieve
        db: Database session
        
    Returns:
        User object with its details (password not included)
        
    Raises:
        HTTPException (404): If the user with the specified ID is not found
        HTTPException (403): If the requester lacks admin privileges
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.user.User)
def update_user(
    user_id: int,
    user: schemas.user.UserUpdate,
    db: Session = Depends(get_db_session)
):
    """Update an existing user account.
    
    Updates the specified user with the provided information. The password
    is hashed if provided. Only fields that are explicitly set in the request
    will be updated. This endpoint is restricted to administrators.
    
    Args:
        user_id: ID of the user to update
        user: Update schema containing fields to update
        db: Database session
        
    Returns:
        Updated user object (password not included)
        
    Raises:
        HTTPException (404): If the user with the specified ID is not found
        HTTPException (403): If the requester lacks admin privileges
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)

    if "password" in update_data:
        if update_data["password"]:
            hashed_password = auth.get_password_hash(update_data["password"])
            db_user.hashed_password = hashed_password
        del update_data["password"] # Remove password from dict before iterating

    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete a user account from the system.
    
    Removes the specified user from the system. This operation cannot be undone.
    This endpoint is restricted to administrators.
    
    Args:
        user_id: ID of the user to delete
        db: Database session
        
    Returns:
        No content (204) if successful
        
    Raises:
        HTTPException (404): If the user with the specified ID is not found
        HTTPException (403): If the requester lacks admin privileges
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Add check: prevent deleting the last admin user?

    db.delete(db_user)
    db.commit()
    return None
