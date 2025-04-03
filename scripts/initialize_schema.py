#!/usr/bin/env python3
"""
Initialize database schema for NetRaven.

This script creates all required database tables and initializes default data.
It runs as part of the container startup process to ensure the database schema
is properly set up before the application starts.
"""

import os
import sys
import asyncio
from pathlib import Path
import time

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from sqlalchemy import inspect, text
from netraven.web.database import engine, init_db, Base
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.scripts.initialize_schema")

# Maximum number of connection retry attempts
MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds

async def wait_for_database():
    """
    Wait for the database to be available.
    
    This function attempts to connect to the database multiple times,
    waiting between attempts. This is useful in container environments
    where the database might not be immediately available.
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Try to connect and execute a simple query
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Database connection attempt {attempt+1}/{MAX_RETRIES} failed: {e}")
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts")
                raise
    
    return False

async def initialize_schema():
    """
    Initialize the database schema.
    
    This function creates all required tables and indexes, then validates
    that the schema was created correctly.
    """
    # First, make sure the database is available
    await wait_for_database()
    
    # Initialize the schema using the web.database init_db function
    # This will create all tables defined in models that use the Base class
    logger.info("Creating database schema")
    
    try:
        await init_db()
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Error creating database schema: {e}")
        sys.exit(1)
    
    # Verify schema was created correctly
    async with engine.begin() as conn:
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        
        # Check for essential tables
        required_tables = [
            "users", "devices", "tags", "credentials", "credential_tags",
            "backups", "job_logs", "job_log_entries", "scheduled_jobs", 
            "admin_settings", "audit_logs"
        ]
        
        missing_tables = []
        for table in required_tables:
            if not await conn.run_sync(lambda sync_conn: inspector.has_table(table)):
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"The following required tables are missing: {', '.join(missing_tables)}")
            sys.exit(1)
        
        # Log table information for debugging
        all_tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())
        logger.info(f"All tables created: {', '.join(all_tables)}")
        
        for table in required_tables:
            columns = await conn.run_sync(lambda sync_conn: inspector.get_columns(table))
            column_names = [column["name"] for column in columns]
            logger.info(f"Table {table} columns: {', '.join(column_names)}")
    
    logger.info("Schema initialization complete")

if __name__ == "__main__":
    try:
        asyncio.run(initialize_schema())
    except Exception as e:
        logger.error(f"Unhandled exception during schema initialization: {e}")
        sys.exit(1) 