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
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise 