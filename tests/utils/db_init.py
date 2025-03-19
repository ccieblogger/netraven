"""
Database initialization utilities for tests.

This module provides functions to initialize and reset the database for testing.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from netraven.db.models import Base, User
from netraven.db.session import get_db
from netraven.core.config import load_config, is_test_env


def get_test_db_url():
    """Get the database URL for testing."""
    config = load_config()
    return config["database"]["url"]


def init_test_db():
    """Initialize the test database with required tables and initial data."""
    if not is_test_env():
        raise RuntimeError("This function should only be called in the test environment")
    
    # Get database URL from config
    db_url = get_test_db_url()
    
    # Create engine and session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create initial test data
    db = SessionLocal()
    try:
        # Create test admin user
        admin_user = User(
            username="testadmin",
            email="testadmin@example.com",
            full_name="Test Admin",
            is_active=True,
            permissions=["admin:*", "read:*", "write:*"]
        )
        admin_user.set_password("testpassword")
        
        # Create regular test user
        regular_user = User(
            username="testuser",
            email="testuser@example.com",
            full_name="Test User",
            is_active=True,
            permissions=["read:devices", "write:devices"]
        )
        regular_user.set_password("testpassword")
        
        db.add(admin_user)
        db.add(regular_user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def reset_test_db():
    """Reset the test database to a clean state."""
    if not is_test_env():
        raise RuntimeError("This function should only be called in the test environment")
    
    init_test_db()


def get_test_db():
    """Get a database session for testing."""
    if not is_test_env():
        raise RuntimeError("This function should only be called in the test environment")
    
    db = next(get_db())
    try:
        yield db
    finally:
        db.close() 