"""
Test script for database migrations.

This script verifies that the database tables are created correctly
with all required fields and indexes.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netraven.web.migrations.test")

def test_migrations():
    """
    Test that migrations have been applied correctly.
    
    Returns:
        True if all tests pass, False otherwise
    """
    # Get database connection details from environment variables
    db_host = os.environ.get("NETRAVEN_WEB_DB_HOST", "localhost")
    db_port = int(os.environ.get("NETRAVEN_WEB_DB_PORT", "5432"))
    db_user = os.environ.get("NETRAVEN_WEB_DB_USER", "netraven")
    db_password = os.environ.get("NETRAVEN_WEB_DB_PASSWORD", "netraven")
    db_name = os.environ.get("NETRAVEN_WEB_DB_NAME", "netraven")
    
    # Create database URL
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Get inspector
        inspector = inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        logger.info(f"Found {len(tables)} tables in the database")
        
        # Check for required tables
        required_tables = [
            'users', 
            'devices', 
            'backups',
            'job_logs',
            'job_log_entries',
            'tags',
            'device_tags'
        ]
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"Error: The following required tables are missing: {', '.join(missing_tables)}")
            return False
        
        logger.info("All required tables exist")
        
        # Check for specific columns in key tables
        if 'devices' in tables:
            device_columns = [column['name'] for column in inspector.get_columns('devices')]
            required_device_columns = ['id', 'name', 'ip_address', 'device_type', 'created_at', 'updated_at']
            
            missing_columns = [col for col in required_device_columns if col not in device_columns]
            if missing_columns:
                logger.error(f"Error: The devices table is missing columns: {', '.join(missing_columns)}")
                return False
        
        if 'backups' in tables:
            backup_columns = [column['name'] for column in inspector.get_columns('backups')]
            if 'serial_number' not in backup_columns:
                logger.warning("Warning: The backups table does not have the serial_number column")
        
        logger.info("Migration verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing migrations: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = test_migrations()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 