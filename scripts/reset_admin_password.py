#!/usr/bin/env python3
"""
Reset the admin password to the default value (EMERGENCY USE ONLY).

This script resets the password for the admin user to "NetRaven".
It should ONLY be used as an emergency recovery measure when admin access is lost.
This is NOT run automatically - it must be manually executed when needed.

Usage:
    python scripts/reset_admin_password.py

SECURITY WARNING: This script should be kept secure and only used by authorized personnel.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from netraven.web.database import SessionLocal, init_db
from netraven.web.crud import get_user_by_username
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.scripts.reset_admin_password")

# Setup password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def reset_admin_password(db: Session, username: str = "admin", password: str = "NetRaven") -> None:
    """
    Reset the password for the admin user.
    
    Args:
        db: Database session
        username: Username of the admin user
        password: New password for the admin user
    """
    # Get the admin user
    admin_user = get_user_by_username(db, username)
    
    if not admin_user:
        logger.error(f"Admin user '{username}' not found")
        return
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Update the admin user's password
    admin_user.password_hash = hashed_password
    db.commit()
    
    logger.info(f"PASSWORD RESET: User '{username}' password has been reset to '{password}'")
    logger.info(f"SECURITY NOTE: For security reasons, you should change this password after login.")

def main():
    """Main entry point for the script."""
    logger.info("EMERGENCY PASSWORD RESET: Resetting admin password to 'NetRaven'")
    logger.info("WARNING: This is an emergency measure and should only be used when admin access is lost")
    
    # Initialize the database
    init_db()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Reset the admin password
        reset_admin_password(db)
    finally:
        db.close()
    
    logger.info("Admin password reset complete")
    logger.info("You can now log in with username 'admin' and password 'NetRaven'")
    logger.info("IMPORTANT: For security reasons, please change this password immediately after login")

if __name__ == "__main__":
    main() 