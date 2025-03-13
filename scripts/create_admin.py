#!/usr/bin/env python3
"""
Create an admin user in the NetRaven database.

This script is used to create an initial admin user in the database
for testing and development purposes.
"""

import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from netraven.web.database import SessionLocal
from netraven.web.models.user import User
from netraven.web.routers.auth import get_password_hash
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.scripts.create_admin")

def create_admin(username: str, password: str, email: str):
    """
    Create an admin user in the database.
    
    Args:
        username: Admin username
        password: Admin password
        email: Admin email
    """
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            logger.info(f"User {username} already exists, updating password")
            existing_user.hashed_password = get_password_hash(password)
            existing_user.email = email
            existing_user.is_admin = True
            existing_user.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"Updated user {username}")
            return
        
        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            full_name="Admin User",
            is_active=True,
            is_admin=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(admin)
        db.commit()
        logger.info(f"Created admin user {username}")
    
    except Exception as e:
        logger.exception(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main entry point for the script."""
    username = "admin"
    password = "adminpass123"
    email = "admin@example.com"
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        password = sys.argv[2]
    if len(sys.argv) > 3:
        email = sys.argv[3]
    
    create_admin(username, password, email)

if __name__ == "__main__":
    main() 