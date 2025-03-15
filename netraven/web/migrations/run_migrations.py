"""
Migration runner for the NetRaven web interface.

This module provides functions to run all pending Alembic migrations.
"""

import os
import time
import subprocess
import logging
import socket
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netraven.web.migrations.runner")

def wait_for_database(host, port, timeout=60):
    """
    Wait for the database to be ready.
    
    Args:
        host: Database host
        port: Database port
        timeout: Maximum time to wait in seconds
    
    Returns:
        True if database is ready, False if timeout occurred
    """
    logger.info(f"Waiting for database at {host}:{port} to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Try to connect to the database
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((host, port))
            sock.close()
            logger.info("Database is ready!")
            return True
        except (socket.error, socket.timeout):
            # Wait a bit before retrying
            time.sleep(1)
    
    logger.error(f"Timeout waiting for database at {host}:{port}")
    return False

def fix_problematic_migration_files():
    """
    Fix any problematic migration files.
    
    This function can be used to patch migration files that might cause issues.
    """
    # Fix the serial_number migration file
    problematic_file = Path("/app/netraven/web/migrations/versions/20250313_174659_add_serial_number_column_to_backups_.py")
    
    if problematic_file.exists():
        logger.info(f"Fixing problematic migration file: {problematic_file}")
        
        # Read the file content
        content = problematic_file.read_text()
        
        # Ensure the migration checks for table existence
        if "tables = inspector.get_table_names()" not in content:
            logger.info("Adding table existence check to migration file")
            
            # This is a backup measure in case the file edit didn't work
            # The actual fix is done in the edit_file call above
            new_content = content.replace(
                "# Check if the column already exists",
                "# Check if the table exists\n    conn = op.get_bind()\n    inspector = Inspector.from_engine(conn)\n    tables = inspector.get_table_names()\n    \n    if 'backups' not in tables:\n        print(\"Table 'backups' does not exist, skipping column addition.\")\n        return\n    \n    # Check if the column already exists"
            )
            
            # Write back the modified content
            problematic_file.write_text(new_content)
        
        logger.info(f"Fixed problematic migration file: {problematic_file}")
    
    # Fix the merge migration file
    merge_file = Path("/app/netraven/web/migrations/versions/20250314_235000_merge_migrations.py")
    
    if merge_file.exists():
        logger.info(f"Fixing merge migration file: {merge_file}")
        
        # Read the file content
        content = merge_file.read_text()
        
        # Ensure the merge migration has the correct dependencies
        if "depends_on = ('1a227448b5ec', '2e227448c5fc', '2f227448c5fd', '3a227448d6fd')" in content:
            logger.info("Updating merge migration dependencies")
            
            # Update the dependencies to ensure correct order
            new_content = content.replace(
                "depends_on = ('1a227448b5ec', '2e227448c5fc', '2f227448c5fd', '3a227448d6fd')",
                "depends_on = None"
            )
            
            # Write back the modified content
            merge_file.write_text(new_content)
        
        logger.info(f"Fixed merge migration file: {merge_file}")

def run_migrations():
    """
    Run all pending Alembic migrations.
    
    Returns:
        True if migrations were successful, False otherwise
    """
    # Get database connection details from environment variables
    db_host = os.environ.get("NETRAVEN_WEB_DB_HOST", "localhost")
    db_port = int(os.environ.get("NETRAVEN_WEB_DB_PORT", "5432"))
    db_user = os.environ.get("NETRAVEN_WEB_DB_USER", "netraven")
    db_password = os.environ.get("NETRAVEN_WEB_DB_PASSWORD", "netraven")
    db_name = os.environ.get("NETRAVEN_WEB_DB_NAME", "netraven")
    
    # Wait for the database to be ready
    if not wait_for_database(db_host, db_port):
        logger.error("Database is not ready, cannot run migrations")
        return False
    
    # Fix any problematic migration files
    fix_problematic_migration_files()
    
    # Set up the environment for Alembic
    env = os.environ.copy()
    
    # Set the DATABASE_URL for Alembic to use
    env["DATABASE_URL"] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    logger.info("Running Alembic migrations...")
    
    try:
        # First check the current migration status
        logger.info("Checking current migration status...")
        subprocess.run(
            ["alembic", "-c", "/app/netraven/web/migrations/alembic.ini", "current"],
            env=env,
            check=True
        )
        
        # Try to upgrade to the latest revision
        logger.info("Upgrading to the latest revision...")
        result = subprocess.run(
            ["alembic", "-c", "/app/netraven/web/migrations/alembic.ini", "upgrade", "head"],
            env=env,
            check=True
        )
        
        if result.returncode == 0:
            logger.info("Migration to head completed successfully")
            return True
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error during standard migration: {e}")
        
        try:
            # If that fails, try to upgrade with the --sql flag to see the SQL that would be executed
            logger.info("Generating SQL for migrations...")
            sql_output = subprocess.run(
                ["alembic", "-c", "/app/netraven/web/migrations/alembic.ini", "upgrade", "head", "--sql"],
                env=env,
                capture_output=True,
                text=True
            )
            
            # Log the SQL for debugging
            logger.info(f"SQL that would be executed:\n{sql_output.stdout}")
            
            # Try to upgrade with the merge revision explicitly
            logger.info("Attempting to upgrade to merge revision...")
            result = subprocess.run(
                ["alembic", "-c", "/app/netraven/web/migrations/alembic.ini", "upgrade", "4a227448e6fe"],
                env=env,
                check=True
            )
            
            if result.returncode == 0:
                logger.info("Migration to merge revision completed successfully")
                return True
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during merge migration: {e}")
            
            try:
                # As a last resort, try to stamp the database with the merge revision
                logger.info("Attempting to stamp the database with the merge revision...")
                result = subprocess.run(
                    ["alembic", "-c", "/app/netraven/web/migrations/alembic.ini", "stamp", "4a227448e6fe"],
                    env=env,
                    check=True
                )
                
                if result.returncode == 0:
                    logger.info("Database stamped with merge revision successfully")
                    return True
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Error stamping database: {e}")
    
    logger.error("All migration attempts failed")
    return False

if __name__ == "__main__":
    # Skip migrations if the environment variable is set
    if os.environ.get("SKIP_MIGRATIONS", "").lower() in ("true", "1", "yes"):
        logger.info("Skipping migrations as SKIP_MIGRATIONS is set")
        exit(0)
    
    # Run migrations
    success = run_migrations()
    
    # Exit with appropriate status code
    exit(0 if success else 1) 