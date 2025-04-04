"""
Asynchronous User Management Service for NetRaven.

Handles creating, retrieving, updating, and deleting users,
including password hashing and permission management logic.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# Models and Schemas
from netraven.web.models.user import User as UserModel
from netraven.web.schemas.user import User, UserCreate, UserUpdate, UpdateNotificationPreferences

# Hashing utility (assuming it exists and is compatible)
# from netraven.core.utils.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)

class AsyncUserService:
    """
    Provides methods for managing user entities asynchronously.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize the user service.

        Args:
            db_session: Async database session.
        """
        self._db_session = db_session

    async def get_user_by_id(self, user_id: str) -> Optional[UserModel]:
        """Fetches a user by their ID."""
        # Placeholder for logic currently in crud.get_user
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        """Fetches a user by their username."""
        # Placeholder for logic currently in crud.get_user_by_username
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        """Fetches a user by their email address."""
        # Placeholder for logic currently in crud.get_user_by_email
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Lists users with pagination."""
        # Placeholder for logic currently in crud.get_users
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self._db_session.execute(stmt)
        return result.scalars().all()

    async def create_user(self, user_data: UserCreate) -> UserModel:
        """Creates a new user."""
        # Placeholder for logic currently in crud.create_user
        # Includes checks for existing username/email and password hashing
        existing_user = await self.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")
        existing_email = await self.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
            
        # TODO: Implement proper password hashing using security utils
        # hashed_password = get_password_hash(user_data.password)
        hashed_password = user_data.password + "-hashed" # Placeholder hash

        db_user = UserModel(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            is_admin=user_data.is_admin,
            permissions=user_data.permissions,
            notification_preferences=user_data.notification_preferences
        )
        self._db_session.add(db_user)
        try:
            await self._db_session.flush() # Use flush to get potential errors before commit
            await self._db_session.refresh(db_user) # Refresh to get DB defaults like ID
            return db_user
        except IntegrityError as e:
            await self._db_session.rollback() # Rollback on error
            logger.error(f"Database integrity error creating user: {e}")
            # More specific error detection could be added here
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists or invalid data.")
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during user creation flush/refresh: {e}")
             raise

    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Optional[UserModel]:
        """Updates an existing user."""
        # Placeholder for logic currently in crud.update_user
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return None # Or raise NotFound

        update_data = user_data
        for key, value in update_data.items():
             # TODO: Add password hashing if 'password' is in update_data
            if hasattr(db_user, key):
                setattr(db_user, key, value)
            else:
                 logger.warning(f"Attempted to update non-existent attribute '{key}' on user {user_id}")

        try:
            await self._db_session.flush()
            await self._db_session.refresh(db_user)
            return db_user
        except Exception as e:
             await self._db_session.rollback()
             logger.error(f"Error during user update flush/refresh: {e}")
             raise

    async def delete_user(self, user_id: str) -> bool:
        """Deletes a user."""
        # Placeholder for logic currently in crud.delete_user
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return False # Indicate not found
        
        await self._db_session.delete(db_user)
        try:
            await self._db_session.flush()
            return True
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error during user deletion flush: {e}")
            raise
        
    async def update_notification_preferences(self, user_id: str, preferences_data: UpdateNotificationPreferences) -> Optional[UserModel]:
        """Updates the notification preferences for a specific user."""
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return None # Indicate not found

        # Ensure the notification_preferences field is a dict
        if db_user.notification_preferences is None or not isinstance(db_user.notification_preferences, dict):
            db_user.notification_preferences = {}
        
        # Get update data, excluding unset fields to avoid overwriting
        update_data = preferences_data.dict(exclude_unset=True)
        
        # Merge the updates into the existing dict
        current_prefs = dict(db_user.notification_preferences) # Create mutable copy
        current_prefs.update(update_data)
        
        # Assign the updated dict back to the user model field
        db_user.notification_preferences = current_prefs
        
        try:
            await self._db_session.flush() # Flush changes
            await self._db_session.refresh(db_user) # Refresh to get any DB updates
            logger.info(f"Updated notification preferences for user {user_id}")
            return db_user
        except Exception as e:
            await self._db_session.rollback()
            logger.error(f"Error updating notification preferences for user {user_id}: {e}")
            # Consider raising a specific service exception here
            raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 detail="Failed to update notification preferences"
            )

    # TODO: Add methods for register_user logic, update_notification_preferences etc. 