#!/usr/bin/env python3
"""
Initialize the NetRaven database with default data.
This script creates:
1. Default admin user
2. Default system tag
"""

import sys
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import project modules
try:
    from netraven.db.session import get_db
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from netraven.db.base import Base
    from netraven.db.models.user import User
    from netraven.db.models.tag import Tag
    from netraven.db.models.device import Device
    from netraven.api.auth import get_password_hash
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

# Default data constants
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",  # This will be hashed
    "email": "admin@netraven.example.com",
    "is_active": True,
    "role": "admin"
}

DEFAULT_TAGS = [
    {
        "name": "default",
        "type": "system"
    }
]

# Try to use a custom db session if we're outside the container
def get_custom_db():
    """Create a custom db session if needed for non-container environment."""
    try:
        # First try the standard session
        yield from get_db()
    except Exception as e:
        logger.warning(f"Standard DB session failed: {e}")
        logger.info("Trying to connect using localhost instead...")
        
        # Create a custom session with localhost connection
        db_url = "postgresql+psycopg2://netraven:netraven@localhost:5432/netraven"
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

def create_admin_user(db):
    """Create the default admin user if it doesn't exist."""
    existing_admin = db.query(User).filter(User.username == DEFAULT_ADMIN["username"]).first()
    
    if existing_admin:
        logger.info(f"Admin user '{DEFAULT_ADMIN['username']}' already exists with ID: {existing_admin.id}")
        return existing_admin
    
    hashed_password = get_password_hash(DEFAULT_ADMIN["password"])
    
    new_admin = User(
        username=DEFAULT_ADMIN["username"],
        hashed_password=hashed_password,
        email=DEFAULT_ADMIN["email"],
        is_active=DEFAULT_ADMIN["is_active"],
        role=DEFAULT_ADMIN["role"]
    )
    
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    logger.info(f"Admin user '{DEFAULT_ADMIN['username']}' created with ID: {new_admin.id}")
    
    return new_admin

def create_default_tags(db):
    """Create default system tags if they don't exist."""
    created_tags = []
    
    for tag_data in DEFAULT_TAGS:
        existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
        
        if existing_tag:
            logger.info(f"Tag '{tag_data['name']}' already exists with ID: {existing_tag.id}")
            created_tags.append(existing_tag)
            continue
        
        new_tag = Tag(
            name=tag_data["name"],
            type=tag_data["type"]
        )
        
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        logger.info(f"Tag '{tag_data['name']}' created with ID: {new_tag.id}")
        created_tags.append(new_tag)
    
    return created_tags

def associate_default_tag_with_devices(db):
    """Associate the default tag with all existing devices that don't have it."""
    try:
        # Get the default tag
        default_tag = db.query(Tag).filter(Tag.name == "default").first()
        
        if not default_tag:
            logger.warning("Default tag not found, cannot associate with devices")
            return
        
        # Find devices without the default tag
        devices_without_tag = (
            db.query(Device)
            .filter(~Device.tags.any(Tag.id == default_tag.id))
            .all()
        )
        
        if not devices_without_tag:
            logger.info("All existing devices already have the default tag")
            return
        
        # Associate the default tag with devices
        for device in devices_without_tag:
            device.tags.append(default_tag)
            logger.info(f"Associated default tag with device: {device.hostname}")
        
        db.commit()
        logger.info(f"Default tag associated with {len(devices_without_tag)} device(s)")
    except Exception as e:
        logger.error(f"Error associating default tag with devices: {e}")

def init_database():
    """Initialize the database with default data."""
    try:
        # Try standard DB session first, then local connection if that fails
        try:
            db = next(get_db())
            logger.info("Connected to database using standard session")
        except Exception as e:
            logger.warning(f"Standard DB session failed: {e}")
            logger.info("Trying to connect using localhost instead...")
            db = next(get_custom_db())
            logger.info("Connected to database using localhost")
        
        # Create default admin user
        create_admin_user(db)
        
        # Create default tags
        create_default_tags(db)
        
        # Associate default tag with existing devices
        associate_default_tag_with_devices(db)
        
        logger.info("Database initialization completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(init_database()) 