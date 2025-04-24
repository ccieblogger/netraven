#!/usr/bin/env python3
"""
Initialize the NetRaven database with default data.
This script creates:
1. Default admin user
2. Default system tag
3. Default admin credential
"""

import sys
import os
import logging
from pathlib import Path
from netraven.utils.unified_logger import get_unified_logger

# Set up logging
logger = get_unified_logger()

# Import project modules
try:
    from netraven.db.session import get_db
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import OperationalError
    from netraven.db.base import Base
    from netraven.db.models.user import User
    from netraven.db.models.tag import Tag
    from netraven.db.models.device import Device
    from netraven.db.models.credential import Credential
    from netraven.api.auth import get_password_hash
    from netraven.db.models.job import Job
except ImportError as e:
    logger.log(
        f"Failed to import required modules: {e}",
        level="ERROR",
        destinations=["stdout"],
        source="db_init_data",
    )
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

DEFAULT_CREDENTIALS = [
    {
        "username": "admin",
        "password": "Password1",  # This will be hashed
        "description": "Default admin credential for device access",
        "priority": 10,  # High priority (lower number)
        "is_system": True
    }
]

# Try to use a custom db session if we're outside the container
def get_custom_db():
    """Create a custom db session if needed for non-container environment."""
    try:
        # First try the standard session
        yield from get_db()
    except Exception as e:
        logger.log(f"Standard DB session failed: {e}", level="WARNING", destinations=["stdout"], source="db_init_data")
        logger.log("Trying to connect using localhost instead...", level="INFO", destinations=["stdout"], source="db_init_data")
        
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
        logger.log(
            f"Admin user '{DEFAULT_ADMIN['username']}' already exists with ID: {existing_admin.id}",
            level="INFO",
            destinations=["stdout"],
            source="db_init_data",
        )
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
    logger.log(
        f"Admin user '{DEFAULT_ADMIN['username']}' created with ID: {new_admin.id}",
        level="INFO",
        destinations=["stdout"],
        source="db_init_data",
    )
    
    return new_admin

def create_default_tags(db):
    """Create default system tags if they don't exist."""
    created_tags = []
    
    for tag_data in DEFAULT_TAGS:
        existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
        
        if existing_tag:
            logger.log(
                f"Tag '{tag_data['name']}' already exists with ID: {existing_tag.id}",
                level="INFO",
                destinations=["stdout"],
                source="db_init_data",
            )
            created_tags.append(existing_tag)
            continue
        
        new_tag = Tag(
            name=tag_data["name"],
            type=tag_data["type"]
        )
        
        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)
        logger.log(
            f"Tag '{tag_data['name']}' created with ID: {new_tag.id}",
            level="INFO",
            destinations=["stdout"],
            source="db_init_data",
        )
        created_tags.append(new_tag)
    
    return created_tags

def create_default_credentials(db):
    """Create default system credentials if they don't exist."""
    created_credentials = []
    
    for cred_data in DEFAULT_CREDENTIALS:
        try:
            # Check if credential already exists using a basic query
            # This avoids referencing columns that might not exist yet
            stmt = text("SELECT id, username FROM credentials WHERE username = :username")
            result = db.execute(stmt, {"username": cred_data["username"]}).first()
            
            if result:
                logger.log(
                    f"Credential with username '{cred_data['username']}' already exists with ID: {result[0]}",
                    level="INFO",
                    destinations=["stdout"],
                    source="db_init_data",
                )
                # Skip to next credential
                continue
                
            # Create with basic fields that are guaranteed to exist
            hashed_password = get_password_hash(cred_data["password"])
            
            # Create the credential with only the basic fields
            new_cred = Credential(
                username=cred_data["username"],
                password=hashed_password,
                priority=cred_data.get("priority", 100)
            )
            
            # Try to set optional fields if schema supports them
            if hasattr(Credential, 'description'):
                new_cred.description = cred_data.get("description")
            if hasattr(Credential, 'is_system'):
                new_cred.is_system = cred_data.get("is_system", False)
            
            db.add(new_cred)
            db.commit()
            db.refresh(new_cred)
            logger.log(
                f"System credential '{cred_data['username']}' created with ID: {new_cred.id}",
                level="INFO",
                destinations=["stdout"],
                source="db_init_data",
            )
            created_credentials.append(new_cred)
            
        except Exception as e:
            logger.log(
                f"Error creating credential: {e}",
                level="ERROR",
                destinations=["stdout"],
                source="db_init_data",
            )
            # Continue with other credentials
            db.rollback()
    
    return created_credentials

def associate_default_tag_with_devices(db):
    """Associate the default tag with all existing devices that don't have it."""
    try:
        # Get the default tag
        default_tag = db.query(Tag).filter(Tag.name == "default").first()
        
        if not default_tag:
            logger.log(
                "Default tag not found, cannot associate with devices",
                level="WARNING",
                destinations=["stdout"],
                source="db_init_data",
            )
            return
        
        # Find devices without the default tag
        devices_without_tag = (
            db.query(Device)
            .filter(~Device.tags.any(Tag.id == default_tag.id))
            .all()
        )
        
        if not devices_without_tag:
            logger.log(
                "All existing devices already have the default tag",
                level="INFO",
                destinations=["stdout"],
                source="db_init_data",
            )
            return
        
        # Associate the default tag with devices
        for device in devices_without_tag:
            device.tags.append(default_tag)
            logger.log(
                f"Associated default tag with device: {device.hostname}",
                level="INFO",
                destinations=["stdout"],
                source="db_init_data",
            )
        
        db.commit()
        logger.log(
            f"Default tag associated with {len(devices_without_tag)} device(s)",
            level="INFO",
            destinations=["stdout"],
            source="db_init_data",
        )
    except Exception as e:
        logger.log(
            f"Error associating default tag with devices: {e}",
            level="ERROR",
            destinations=["stdout"],
            source="db_init_data",
        )

def associate_default_credential_with_default_tag(db):
    """Associate the default credential with the default tag."""
    try:
        # Get the default tag
        default_tag = db.query(Tag).filter(Tag.name == "default").first()
        if not default_tag:
            logger.log(
                "Default tag not found, cannot associate with credential",
                level="WARNING",
                destinations=["stdout"],
                source="db_init_data",
            )
            return
        
        # Get the default credential
        default_cred = db.query(Credential).filter(Credential.username == "admin").first()
        if not default_cred:
            logger.log(
                "Default credential not found, cannot associate with tag",
                level="WARNING",
                destinations=["stdout"],
                source="db_init_data",
            )
            return
        
        # Check if the association already exists
        if default_tag in default_cred.tags:
            logger.log(
                "Default credential is already associated with default tag",
                level="INFO",
                destinations=["stdout"],
                source="db_init_data",
            )
            return
        
        # Associate the default tag with the default credential
        default_cred.tags.append(default_tag)
        db.commit()
        
        logger.log(
            f"Successfully associated default credential (ID: {default_cred.id}) with default tag (ID: {default_tag.id})",
            level="INFO",
            destinations=["stdout"],
            source="db_init_data",
        )
    except Exception as e:
        logger.log(
            f"Error associating default credential with default tag: {e}",
            level="ERROR",
            destinations=["stdout"],
            source="db_init_data",
        )
        db.rollback()

def create_system_reachability_job(db):
    """Create the system reachability job if it doesn't exist, associated with the default tag."""
    # Check for existing job
    job = db.query(Job).filter(Job.name == "system-reachability", Job.is_system_job == True).first()
    if job:
        logger.log(
            f"System reachability job already exists with ID: {job.id}",
            level="INFO",
            destinations=["stdout"],
            source="db_init_data",
        )
        return job
    # Get default tag
    default_tag = db.query(Tag).filter(Tag.name == "default").first()
    if not default_tag:
        logger.log(
            "Default tag not found, cannot create system reachability job",
            level="WARNING",
            destinations=["stdout"],
            source="db_init_data",
        )
        return None
    # Create the job
    job = Job(
        name="system-reachability",
        description="System job: checks device reachability via ICMP and TCP.",
        job_type="reachability",
        is_enabled=True,
        is_system_job=True,
        tags=[default_tag]
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.log(
        f"System reachability job created with ID: {job.id}",
        level="INFO",
        destinations=["stdout"],
        source="db_init_data",
    )
    return job

def init_database():
    """Initialize the database with default data."""
    try:
        # Try standard DB session first, then local connection if that fails
        try:
            db = next(get_db())
            logger.log("Connected to database using standard session", level="INFO", destinations=["stdout"], source="db_init_data")
        except Exception as e:
            logger.log(f"Standard DB session failed: {e}", level="WARNING", destinations=["stdout"], source="db_init_data")
            logger.log("Trying to connect using localhost instead...", level="INFO", destinations=["stdout"], source="db_init_data")
            db = next(get_custom_db())
            logger.log("Connected to database using localhost", level="INFO", destinations=["stdout"], source="db_init_data")
        
        # Create default admin user
        create_admin_user(db)
        
        # Create default tags
        create_default_tags(db)
        
        # Create default credentials
        create_default_credentials(db)
        
        # Associate default tag with existing devices
        associate_default_tag_with_devices(db)
        
        # Associate default credential with default tag
        associate_default_credential_with_default_tag(db)
        
        # Create system reachability job
        create_system_reachability_job(db)
        
        logger.log("Database initialization completed successfully", level="INFO", destinations=["stdout"], source="db_init_data")
        return 0
    except Exception as e:
        logger.log(f"Database initialization failed: {e}", level="ERROR", destinations=["stdout"], source="db_init_data")
        return 1

if __name__ == "__main__":
    sys.exit(init_database()) 