"""
Database connection module for NetRaven.

This module provides SQLAlchemy database connection and session management
for the NetRaven web interface.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from pathlib import Path
from typing import Dict, Any, Generator
from datetime import datetime

# Import internal modules
from netraven.core.config import get_default_config_path, load_config
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.web.database")

# Load configuration
config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Get database configuration
db_config = config["web"]["database"]
db_type = db_config["type"]

# Create database URL based on configuration
if db_type == "sqlite":
    db_path = db_config["sqlite"]["path"]
    # Make sure the path is absolute
    if not os.path.isabs(db_path):
        # Use the current working directory as base, not the config directory
        db_path = os.path.abspath(db_path)
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
elif db_type == "postgres":
    pg_config = db_config["postgres"]
    DATABASE_URL = f"postgresql://{pg_config['user']}:{pg_config['password']}@{pg_config['host']}:{pg_config['port']}/{pg_config['database']}"
elif db_type == "mysql":
    mysql_config = db_config["mysql"]
    DATABASE_URL = f"mysql+pymysql://{mysql_config['user']}:{mysql_config['password']}@{mysql_config['host']}:{mysql_config['port']}/{mysql_config['database']}"
else:
    raise ValueError(f"Unsupported database type: {db_type}")

# Create SQLAlchemy engine
# For SQLite, connect_args={"check_same_thread": False} allows using the connection in multiple threads
connect_args = {}
if db_type == "sqlite":
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=config["web"].get("debug", False)  # Echo SQL to stdout in debug mode
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Default tag ID and constants
DEFAULT_TAG_ID = "tag-default"
DEFAULT_TAG_NAME = "Default"
DEFAULT_TAG_COLOR = "#6366F1"  # Indigo color
DEFAULT_TAG_DESCRIPTION = "Default tag for all devices"

def create_default_tag_if_not_exists():
    """
    Ensures the default tag exists in the database.
    This function creates the default tag if it doesn't already exist.
    """
    from netraven.web.models.tag import Tag
    from netraven.web.crud.tag import get_tag_by_name
    
    db = SessionLocal()
    try:
        # Check if default tag exists
        default_tag = get_tag_by_name(db, DEFAULT_TAG_NAME)
        
        if not default_tag:
            logger.info("Creating default tag in database")
            # Create default tag
            default_tag = Tag(
                id=DEFAULT_TAG_ID,
                name=DEFAULT_TAG_NAME,
                description=DEFAULT_TAG_DESCRIPTION,
                color=DEFAULT_TAG_COLOR,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(default_tag)
            db.commit()
            logger.info(f"Default tag created with ID: {DEFAULT_TAG_ID}")
        else:
            logger.info(f"Default tag already exists with ID: {default_tag.id}")
            
            # If the default tag exists but has a different ID, update it
            if default_tag.id != DEFAULT_TAG_ID:
                logger.info(f"Updating default tag ID from {default_tag.id} to {DEFAULT_TAG_ID}")
                # This is risky as it might break existing relationships
                # Only do this if absolutely necessary
                # default_tag.id = DEFAULT_TAG_ID
                # db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating default tag: {e}")
    finally:
        db.close()

def get_db() -> Generator:
    """
    Get database session.
    
    This is a dependency for FastAPI endpoints that need database access.
    
    Yields:
        SQLAlchemy session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database.
    
    This creates all tables if they don't exist.
    """
    from netraven.web.models import user, device, backup, tag  # Import models to register them with Base
    
    logger.info(f"Initializing database at {DATABASE_URL}")
    try:
        Base.metadata.create_all(bind=engine)
        create_default_tag_if_not_exists()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise 