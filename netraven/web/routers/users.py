"""
Users router for managing user accounts.

This module provides endpoints for creating, retrieving, updating, and
deleting user accounts, as well as managing user preferences and passwords.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any

from netraven.web.database import get_async_session
from netraven.web.schemas.user import (
    User, 
    UserCreate, 
    UserUpdate, 
    ChangePassword, 
    UpdateNotificationPreferences
)
from netraven.web.auth import UserPrincipal, get_current_principal, optional_auth
from netraven.web.auth.permissions import (
    require_scope, 
    require_admin, 
    require_self_or_admin
)
from netraven.core.logging import get_logger
from netraven.core.services.service_factory import ServiceFactory

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])

# Helper function to extract user ID for permission checks
async def get_user_id(
    user_id: str = Path(..., description="The ID of the user"),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> str:
    """
    Extract the user ID for permission checking.
    
    Args:
        user_id: The user ID
        session: Database session
        factory: Service factory
        
    Returns:
        str: ID of the user
    """
    return user_id

@router.get("/me", response_model=User)
async def get_current_user(
    principal: UserPrincipal = Depends(get_current_principal)
) -> Dict[str, Any]:
    """
    Get the current authenticated user's profile.
    """
    try:
        logger.info(f"Access granted: user={principal.username}, resource=users/me, action=get")
        return principal.user
    except Exception as e:
        logger.error(f"Error retrieving current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving current user: {str(e)}"
        )

@router.get("/", response_model=List[User])
async def list_users(
    skip: int = Query(0, description="Number of records to skip", ge=0),
    limit: int = Query(100, description="Maximum number of records to return", ge=1, le=1000),
    principal: UserPrincipal = Depends(require_scope("admin:users")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> List[User]:
    """
    List all users.
    
    This endpoint requires the admin:users scope.
    """
    try:
        users = await factory.user_service.list_users(skip=skip, limit=limit)
        
        logger.info(f"Access granted: user={principal.username}, resource=users, action=list, count={len(users)}")
        return users
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_self_or_admin(get_user_id))
) -> User:
    """
    Get a user by ID.
    
    This endpoint requires either the admin:users scope or the requesting user
    to be the same as the requested user.
    """
    try:
        user = await factory.user_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        logger.info(f"Access granted: user={principal.username}, resource=user:{user_id}, action=get")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_self_or_admin(get_user_id))
) -> User:
    """
    Update a user.
    
    This endpoint requires either the admin:users scope or the requesting user
    to be the same as the user being updated.
    
    Regular users cannot grant themselves admin privileges or deactivate their accounts.
    """
    try:
        # Prevent non-admins from making themselves admin or changing active status
        if not principal.is_admin:
            if user_data.is_admin is not None and user_data.is_admin:
                logger.warning(f"Access denied: user={principal.username} attempted to grant admin to {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Cannot grant admin privileges"
                )
            if user_data.is_active is not None and not user_data.is_active:
                logger.warning(f"Access denied: user={principal.username} attempted to deactivate {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Cannot deactivate user"
                )
        
        # Call the service to update the user
        updated_user = await factory.user_service.update_user(
            user_id, 
            user_data.model_dump(exclude_unset=True)
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        logger.info(f"User updated: id={user_id}, user={principal.username}")
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    principal: UserPrincipal = Depends(require_scope("admin:users")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
):
    """
    Delete a user.
    
    This endpoint requires the admin:users scope.
    Users cannot delete themselves.
    """
    try:
        # Prevent self-deletion
        if principal.id == user_id:
            logger.warning(f"Access denied: user={principal.username} attempted self-deletion")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Users cannot delete themselves"
            )

        result = await factory.user_service.delete_user(user_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )

        logger.info(f"User deleted: id={user_id}, user={principal.username}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    principal: UserPrincipal = Depends(require_scope("admin:users")),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory)
) -> User:
    """
    Create a new user.
    
    This endpoint requires the admin:users scope.
    """
    try:
        new_user = await factory.user_service.create_user(user_data)
        
        logger.info(f"User created: id={new_user.id}, username={new_user.username}, user={principal.username}")
        return new_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {str(e)}"
        )

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    factory: ServiceFactory = Depends(ServiceFactory),
    session: AsyncSession = Depends(get_async_session),
    principal: Optional[UserPrincipal] = Depends(optional_auth())
) -> User:
    """
    Register a new user without requiring authentication (if enabled).
    
    This endpoint allows self-registration if enabled in the system settings.
    """
    try:
        # TODO: Get this setting from config/environment variable
        allow_self_registration = True 
        is_admin_request = principal is not None and (principal.is_admin or principal.has_scope("admin:users"))

        # Check if registration is allowed
        if not allow_self_registration and not is_admin_request:
            logger.warning(f"Self-registration attempt failed: Registration is disabled")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Self-registration is disabled"
            )

        # For security, enforce non-admin status for self-registered users
        if not is_admin_request:
            user_data.is_admin = False

        # Create the user with limited active status based on config
        # TODO: Get auto_activate setting from config
        auto_activate = True
        if not is_admin_request and not auto_activate:
            user_data.is_active = False

        new_user = await factory.user_service.create_user(user_data)
        
        # Log the registration
        requester = "admin" if is_admin_request else "self-registration"
        logger.info(f"User registered: id={new_user.id}, username={new_user.username}, requestor={requester}")
        
        return new_user
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error registering user: {str(e)}"
        )

@router.patch("/{user_id}/password", status_code=status.HTTP_200_OK)
async def change_password(
    user_id: str,
    password_data: ChangePassword,
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_self_or_admin(get_user_id))
) -> Dict[str, str]:
    """
    Change a user's password.
    
    This endpoint requires either the admin:users scope or the requesting user
    to be the same as the user whose password is being changed.
    
    Admins can change passwords without providing the current password.
    """
    try:
        is_self = principal.id == user_id
        admin_bypass = principal.is_admin and not is_self
        
        # Admins don't need to provide current password
        if is_self and not password_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required"
            )
            
        # Verify current password if this is a self-change
        if is_self and not admin_bypass:
            # Call service to validate the current password
            valid = await factory.user_service.validate_password(
                user_id, 
                password_data.current_password
            )
            if not valid:
                logger.warning(f"Password change failed: id={user_id}, user={principal.username}, reason=invalid_current_password")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect"
                )
        
        # Call service to update the password
        success = await factory.user_service.update_password(
            user_id, 
            password_data.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        action_type = "admin_reset" if admin_bypass else "self_change"
        logger.info(f"Password changed: id={user_id}, user={principal.username}, action={action_type}")
        
        return {
            "status": "success",
            "message": "Password successfully updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

@router.patch("/{user_id}/notification-preferences", response_model=User)
async def update_notification_preferences(
    user_id: str,
    preferences: UpdateNotificationPreferences,
    principal: UserPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_async_session),
    factory: ServiceFactory = Depends(ServiceFactory),
    _: str = Depends(require_self_or_admin(get_user_id))
) -> User:
    """
    Update a user's notification preferences.
    
    This endpoint requires either the admin:users scope or the requesting user
    to be the same as the user whose preferences are being updated.
    """
    try:
        updated_user = await factory.user_service.update_notification_preferences(
            user_id, 
            preferences.model_dump()
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        logger.info(f"Notification preferences updated: id={user_id}, user={principal.username}")
        return updated_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating notification preferences: {str(e)}"
        )

# Clean up unused imports if all endpoints are refactored
# from sqlalchemy.orm import Session
# from netraven.web.database import get_db 