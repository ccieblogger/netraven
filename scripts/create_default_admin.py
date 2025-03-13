#!/usr/bin/env python3
"""
Create the default admin user for the NetRaven application.

This script creates the default admin user with username 'admin' and password 'NetRaven'.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from netraven.web.database import SessionLocal, init_db
from netraven.web.startup import ensure_default_admin
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.scripts.create_default_admin")

def main():
    """Main entry point for the script."""
    logger.info("Creating default admin user (username: admin, password: NetRaven)")
    
    # Initialize the database
    init_db()
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Ensure the default admin user exists
        ensure_default_admin(db)
    finally:
        db.close()
    
    logger.info("Default admin user creation complete")
    logger.info("You can now log in with username 'admin' and password 'NetRaven'")

if __name__ == "__main__":
    main() 