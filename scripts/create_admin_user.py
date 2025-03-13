#!/usr/bin/env python3
"""
Create an admin user for the NetRaven application.

This script adds an admin user to the database for testing and development purposes.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import argparse
from datetime import datetime

from netraven.web.database import SessionLocal, init_db
from netraven.web.models.user import User
from netraven.web.crud import get_user_by_username, create_user
from netraven.web.schemas.user import UserCreate
from netraven.core.logging import get_logger

# Setup password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create logger
logger = get_logger("netraven.scripts.create_admin_user")

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_admin_user(
    db: Session, 
    username: str, 
    password: str, 
    email: str, 
    full_name: str = "Admin User",
    force: bool = False
) -> None:
    """
    Create an admin user in the database.
    
    Args:
        db: Database session
        username: Username for the admin user
        password: Password for the admin user
        email: Email for the admin user
        full_name: Full name for the admin user
        force: Force create/update even if user exists
    """
    # Check if user already exists
    existing_user = get_user_by_username(db, username)
    
    if existing_user and not force:
        logger.info(f"User {username} already exists. Use --force to update.")
        return
    
    if existing_user and force:
        # Update existing user
        logger.info(f"Updating existing user {username}")
        existing_user.email = email
        existing_user.full_name = full_name
        existing_user.hashed_password = get_password_hash(password)
        existing_user.is_admin = True
        existing_user.is_active = True
        existing_user.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Updated user {username}")
        return
    
    # Create new user
    user_data = UserCreate(
        username=username,
        email=email,
        full_name=full_name,
        is_admin=True,
        is_active=True
    )
    
    # Hash the password
    hashed_password = get_password_hash(password)
    
    # Create the user
    user = create_user(db, user_data, hashed_password)
    
    logger.info(f"Created admin user: {username}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create an admin user for NetRaven")
    parser.add_argument("--username", default="admin", help="Username for the admin user")
    parser.add_argument("--password", default="adminpassword", help="Password for the admin user")
    parser.add_argument("--email", default="admin@example.com", help="Email for the admin user")
    parser.add_argument("--full-name", default="Admin User", help="Full name for the admin user")
    parser.add_argument("--force", action="store_true", help="Force create/update even if user exists")
    
    args = parser.parse_args()
    
    # Initialize the database
    init_db()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Create the admin user
        create_admin_user(
            db=db,
            username=args.username,
            password=args.password,
            email=args.email,
            full_name=args.full_name,
            force=args.force
        )
    finally:
        db.close()
    
    logger.info("Admin user creation complete")

if __name__ == "__main__":
    main() 