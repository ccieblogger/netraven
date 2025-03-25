#!/usr/bin/env python3
"""
Script to run database migrations.

This script runs Alembic migrations to update the database schema.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from netraven.web.database import SessionLocal, Base

def run_migrations():
    """Run database migrations using Alembic."""
    # Get the absolute path to the alembic.ini file
    alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../alembic.ini"))
    if not os.path.exists(alembic_ini_path):
        alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../netraven/web/alembic.ini"))
    
    if not os.path.exists(alembic_ini_path):
        print(f"Error: Could not find alembic.ini in either location.")
        return False
    
    # Create an Alembic configuration
    alembic_cfg = Config(alembic_ini_path)
    
    try:
        # Run the upgrade to the latest revision
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully.")
        return True
    except Exception as e:
        print(f"Error running migrations: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1) 