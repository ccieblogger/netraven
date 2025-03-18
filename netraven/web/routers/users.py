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
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_user_access
)
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
    if not current_principal.has_scope("admin:users") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=users, scope=admin:users, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin:users required"
        )
    
    users = get_users(db)
    logger.info(f"Access granted: user={current_principal.username}, resource=users, scope=admin:users")
    return users

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
    # Use check_user_access to handle permission checks
    user = check_user_access(
        principal=current_principal,
        user_id_or_obj=user_id,
        required_scope="admin:users",
        db=db,
        allow_self_access=True
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
    # Use check_user_access to handle permission checks
    existing_user = check_user_access(
        principal=current_principal,
        user_id_or_obj=user_id,
        required_scope="admin:users",
        db=db,
        allow_self_access=True
    )
    
    # Update user
    updated_user = update_user(db, user_id, user_data.dict(exclude_unset=True))
    logger.info(f"User {user_id} updated by {current_principal.username}")
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
    # Use check_user_access to handle permission checks, but don't allow self-access
    existing_user = check_user_access(
        principal=current_principal,
        user_id_or_obj=user_id,
        required_scope="admin:users",
        db=db,
        allow_self_access=False  # Users shouldn't delete themselves
    )
    
    # Delete user
    delete_user(db, user_id)
    logger.info(f"User {user_id} deleted by {current_principal.username}") 