"""
Users router for the NetRaven web interface.

This module provides user-related endpoints for the API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from netraven.web.database import get_db
from netraven.web.models.user import User as UserModel
from netraven.web.schemas.user import User, UserCreate, UserUpdate
from netraven.web.crud import get_user, get_users, update_user, delete_user
from netraven.web.routers.auth import get_current_active_user, get_current_admin_user
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.routers.users")

# Create router
router = APIRouter()

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """Get current user information."""
    return current_user

@router.get("/", response_model=List[User])
async def read_users(
    skip: int = 0, 
    limit: int = 100,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> List[UserModel]:
    """
    Get all users.
    
    This endpoint requires admin privileges.
    """
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Get a specific user by ID.
    
    This endpoint requires admin privileges.
    """
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: str,
    user: UserUpdate,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> UserModel:
    """
    Update a user.
    
    This endpoint requires admin privileges.
    """
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = update_user(db, db_user=db_user, user=user)
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    current_user: UserModel = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a user.
    
    This endpoint requires admin privileges.
    """
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    delete_user(db, user_id=user_id)
    return None 