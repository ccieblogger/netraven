"""
Users router for the NetRaven web interface.

This module provides user-related endpoints for the API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from netraven.web.database import get_db
from netraven.web.models.user import User as UserModel
from netraven.web.schemas.user import User, UserCreate, UserUpdate
from netraven.web.crud import get_user, get_users, update_user, delete_user
from netraven.web.auth import get_current_principal, UserPrincipal, require_scope
from netraven.web.models.auth import User
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.routers.users")

# Create router
router = APIRouter(prefix="")

@router.get("/me", response_model=User)
async def get_current_user_endpoint(
    current_principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Get the current user.
    
    Args:
        current_principal: The authenticated user
        
    Returns:
        Dict[str, Any]: Current user details
    """
    return current_principal.user

@router.get("/", response_model=List[User])
async def list_users(
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all users.
    
    Args:
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        List[Dict[str, Any]]: List of users
    """
    if not current_principal.has_scope("admin:users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to list users"
        )
    return get_users(db)

@router.get("/{user_id}", response_model=User)
async def get_user_endpoint(
    user_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a user by ID.
    
    Args:
        user_id: The user ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: User details
        
    Raises:
        HTTPException: If the user is not found or current user is not authorized
    """
    # Check if user is admin or getting their own profile
    if not current_principal.has_scope("admin:users") and user_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: str,
    user_data: UserUpdate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update a user.
    
    Args:
        user_id: The user ID
        user_data: The updated user data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Updated user details
        
    Raises:
        HTTPException: If the user is not found or current user is not authorized
    """
    # Check if user is admin or updating their own profile
    if not current_principal.has_scope("admin:users") and user_id != current_principal.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    # Check if user exists
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update user
    updated_user = update_user(db, user_id, user_data.dict(exclude_unset=True))
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a user.
    
    Args:
        user_id: The user ID
        current_principal: The authenticated user
        db: Database session
        
    Raises:
        HTTPException: If the user is not found or current user is not authorized
    """
    if not current_principal.has_scope("admin:users"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete users"
        )
    
    # Check if user exists
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Delete user
    delete_user(db, user_id) 