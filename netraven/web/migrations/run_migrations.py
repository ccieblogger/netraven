"""
Migration runner for the NetRaven web interface.

This module provides functions to run all pending Alembic migrations.
It's a thin wrapper around Alembic that can be called from Python.
"""

import os
import subprocess
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netraven.web.migrations.runner")

def run_migrations():
    """
    Run all pending Alembic migrations.
    
    Returns:
        True if migrations were successful, False otherwise
    """
    logger.info("Running Alembic migrations...")
    
    # Get the path to the alembic.ini file
    alembic_ini_path = Path(__file__).parent / "alembic.ini"
    
    try:
        # Run the alembic upgrade command
        result = subprocess.run(
            ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
            check=True
        )
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            return True
        else:
            logger.error(f"Migrations failed with return code {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    # Run the migrations
    success = run_migrations()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 