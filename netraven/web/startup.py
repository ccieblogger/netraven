"""
Startup script for the NetRaven application.

This module contains functions that run on application startup.
"""

from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime

from netraven.web.models.user import User
from netraven.web.crud import get_user_by_username, create_user, initialize_default_settings
from netraven.web.schemas.user import UserCreate
from netraven.core.logging import get_logger

# Setup password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create logger
logger = get_logger("netraven.web.startup")

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def ensure_default_admin(db: Session) -> None:
    """
    Ensure that the default admin user exists.
    
    This function checks if the default admin user exists and creates it if it doesn't.
    The default credentials are:
    - Username: admin
    - Password: NetRaven
    
    Args:
        db: Database session
    """
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "NetRaven"
    DEFAULT_ADMIN_EMAIL = "admin@netraven.local"
    
    # Check if default admin user already exists
    existing_user = get_user_by_username(db, DEFAULT_ADMIN_USERNAME)
    
    if existing_user:
        logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' already exists.")
        return
    
    # Create new default admin user
    logger.info(f"Creating default admin user '{DEFAULT_ADMIN_USERNAME}'")
    
    try:
        # Create UserCreate object with all required fields including password
        user_data = UserCreate(
            username=DEFAULT_ADMIN_USERNAME,
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            is_admin=True,
            is_active=True
        )
        
        # Create the user
        user = create_user(db, user_data)
        
        logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' created successfully.")
        logger.info(f"You can log in with username '{DEFAULT_ADMIN_USERNAME}' and password '{DEFAULT_ADMIN_PASSWORD}'")
    except Exception as e:
        logger.error(f"Error creating default admin user: {e}")
        # Continue execution even if user creation fails
        # This allows the application to start even if there's an issue with user creation

def initialize_admin_settings(db: Session) -> None:
    """
    Initialize admin settings if they don't exist.
    
    This function ensures that default admin settings are created in the database.
    
    Args:
        db: Database session
    """
    logger.info("Initializing admin settings")
    
    try:
        # Initialize default settings
        settings = initialize_default_settings(db)
        
        if settings:
            logger.info(f"Initialized {len(settings)} admin settings")
        else:
            logger.info("Admin settings were already initialized")
            
    except Exception as e:
        logger.error(f"Error initializing admin settings: {e}")
        # Continue execution even if settings initialization fails 