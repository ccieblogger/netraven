"""
Users router for the NetRaven web interface.

This module provides user-related endpoints for the API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from netraven.web.database import get_db
from netraven.web.models.user import User as UserModel
from netraven.web.schemas.user import User, UserCreate, UserUpdate
from netraven.web.crud import get_user, get_users, update_user, delete_user, create_user, get_user_by_username, get_user_by_email
from netraven.web.auth import (
    get_current_principal, 
    UserPrincipal, 
    require_scope,
    check_user_access,
    optional_auth
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
    try:
        # No permission check needed - users can always access their own profile
        logger.info(f"Access granted: user={current_principal.username}, resource=users/me, action=get")
        return current_principal.user
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error retrieving current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving current user: {str(e)}"
        )

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
    # Standardized permission check
    if not current_principal.has_scope("admin:users") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=users, scope=admin:users, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin:users required"
        )
    
    try:
        users = get_users(db)
        logger.info(f"Access granted: user={current_principal.username}, resource=users, scope=admin:users, count={len(users)}")
        return users
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )

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
    try:
        # Use check_user_access to handle permission checks
        user = check_user_access(
            principal=current_principal,
            user_id_or_obj=user_id,
            required_scope="admin:users",
            db=db,
            allow_self_access=True
        )
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=user:{user_id}, scope=admin:users, action=get")
        return user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error retrieving user details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user details: {str(e)}"
        )

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
    try:
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
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=user:{user_id}, scope=admin:users, action=update")
        return updated_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

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
    try:
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
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=user:{user_id}, scope=admin:users, action=delete")
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_data: UserCreate,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        user_data: The user data
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Created user details
        
    Raises:
        HTTPException: If the user already exists or current user is not authorized
    """
    # Standardized permission check
    if not current_principal.has_scope("admin:users") and not current_principal.is_admin:
        logger.warning(f"Access denied: user={current_principal.username}, " 
                     f"resource=users, scope=admin:users, reason=insufficient_permissions")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions: admin:users required"
        )
    
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            logger.warning(f"User creation failed: user={current_principal.username}, " 
                         f"username={user_data.username}, reason=username_exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{user_data.username}' already exists"
            )
        
        # Create user
        new_user = create_user(db, user_data)
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=users, scope=admin:users, action=create")
        return new_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    # Use optional_auth to check if a user is authenticated
    current_principal: Optional[UserPrincipal] = Depends(optional_auth())
) -> Dict[str, Any]:
    """
    Register a new user without requiring authentication.
    This endpoint can be configured to be enabled/disabled based on application settings.
    
    Args:
        user_data: The user data
        db: Database session
        current_principal: The authenticated user (optional)
        
    Returns:
        Dict[str, Any]: Created user details
        
    Raises:
        HTTPException: If the user already exists or registration is disabled
    """
    # Check if self-registration is enabled (based on configuration)
    # This could be controlled via environment variables or configuration settings
    allow_self_registration = True  # This should come from configuration
    
    # If self-registration is disabled, only admins can register users
    if not allow_self_registration:
        if not current_principal or (not current_principal.has_scope("admin:users") and not current_principal.is_admin):
            logger.warning(f"Self-registration is disabled and user does not have admin permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-registration is disabled. Please contact an administrator."
            )
    
    try:
        # Check if username already exists
        existing_user = get_user_by_username(db, user_data.username)
        if existing_user:
            logger.warning(f"User registration failed: username={user_data.username}, reason=username_exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with username '{user_data.username}' already exists"
            )
        
        # Check if email already exists
        existing_email = get_user_by_email(db, user_data.email)
        if existing_email:
            logger.warning(f"User registration failed: email={user_data.email}, reason=email_exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{user_data.email}' already exists"
            )
        
        # Set default permissions and admin status for self-registered users
        # By default, self-registered users should not be admins
        if not current_principal or not current_principal.is_admin:
            user_data.is_admin = False
        
        # Create user
        new_user = create_user(db, user_data)
        
        # Log the registration
        logger.info(f"User registered successfully: username={user_data.username}")
        
        return new_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        logger.warning(f"User registration failed due to integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering user: {str(e)}"
        ) 