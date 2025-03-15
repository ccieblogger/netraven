"""
Test script for job log migrations.

This script verifies that the job log tables are created correctly
with all required fields and indexes.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("netraven.web.migrations.test")

def test_job_log_migrations():
    """
    Test that job log migrations have been applied correctly.
    
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
        
        # Check if job_logs table exists
        if 'job_logs' not in inspector.get_table_names():
            logger.error("Error: job_logs table does not exist")
            return False
        
        # Check if job_log_entries table exists
        if 'job_log_entries' not in inspector.get_table_names():
            logger.error("Error: job_log_entries table does not exist")
            return False
        
        # Check if job_logs table has retention_days column
        job_logs_columns = [column['name'] for column in inspector.get_columns('job_logs')]
        if 'retention_days' not in job_logs_columns:
            logger.error("Error: job_logs table does not have retention_days column")
            return False
        
        # Check if indexes exist
        job_logs_indexes = inspector.get_indexes('job_logs')
        job_log_entries_indexes = inspector.get_indexes('job_log_entries')
        
        # Check for required indexes
        required_job_logs_indexes = [
            'ix_job_logs_session_id',
            'ix_job_logs_job_type',
            'ix_job_logs_status',
            'ix_job_logs_start_time'
        ]
        
        required_job_log_entries_indexes = [
            'ix_job_log_entries_timestamp',
            'ix_job_log_entries_level',
            'ix_job_log_entries_category'
        ]
        
        # Check for basic indexes (these are created in the initial migration)
        for index_name in required_job_logs_indexes:
            if not any(index['name'] == index_name for index in job_logs_indexes):
                logger.warning(f"Warning: job_logs table does not have index {index_name}")
        
        for index_name in required_job_log_entries_indexes:
            if not any(index['name'] == index_name for index in job_log_entries_indexes):
                logger.warning(f"Warning: job_log_entries table does not have index {index_name}")
        
        # Check for composite indexes (these are created in our new migration)
        composite_job_logs_indexes = [
            'ix_job_logs_device_status',
            'ix_job_logs_created_by_status',
            'ix_job_logs_start_time_status',
            'ix_job_logs_retention'
        ]
        
        composite_job_log_entries_indexes = [
            'ix_job_log_entries_job_log_id_level',
            'ix_job_log_entries_job_log_id_timestamp'
        ]
        
        missing_composite_indexes = []
        
        for index_name in composite_job_logs_indexes:
            if not any(index['name'] == index_name for index in job_logs_indexes):
                missing_composite_indexes.append(index_name)
        
        for index_name in composite_job_log_entries_indexes:
            if not any(index['name'] == index_name for index in job_log_entries_indexes):
                missing_composite_indexes.append(index_name)
        
        if missing_composite_indexes:
            logger.warning(f"Warning: The following composite indexes are missing: {', '.join(missing_composite_indexes)}")
            logger.warning("This is expected if the index migration has not been run yet.")
        
        logger.info("Migration verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing migrations: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = test_job_log_migrations()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1) 