#!/usr/bin/env python3
"""
Ensure database schema is properly initialized with all required columns.

This script checks the database schema and ensures all required columns exist,
with a focus on columns that might be missing in new installations.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from sqlalchemy import inspect, text
from netraven.web.database import engine, init_db, Base
from netraven.core.logging import get_logger
from netraven.web.models.user import User
from netraven.web.models.audit_log import AuditLog

# Create logger
logger = get_logger("netraven.scripts.ensure_schema")

async def ensure_schema():
    """
    Ensure that the database schema has all required columns.
    
    This function checks if required columns exist in the database and creates them if they don't.
    """
    # For async engines, we need to get a connection and use run_sync
    async with engine.begin() as conn:
        # Get inspector through run_sync
        inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
        
        # Initialize database - this will create tables that don't exist
        logger.info("Initializing database schema")
        await init_db()
        
        # Check if tables exist after initialization
        if not await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("users")):
            logger.error("Users table does not exist after initialization")
            sys.exit(1)
            
        if not await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("audit_logs")):
            logger.error("Audit logs table does not exist after initialization")
            sys.exit(1)
        
        logger.info("Database schema successfully initialized")
        
        # Check and report column existence (useful for debugging)
        users_columns = [column["name"] for column in await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("users"))]
        logger.info(f"Users table columns: {', '.join(users_columns)}")
        
        audit_columns = [column["name"] for column in await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns("audit_logs"))]
        logger.info(f"Audit logs table columns: {', '.join(audit_columns)}")
        
        # If we're using PostgreSQL, ensure JSONB columns are properly created
        if engine.dialect.name == "postgresql":
            # Check if notification_preferences column exists with the right type
            if "notification_preferences" not in users_columns:
                logger.info("Adding notification_preferences column to users table")
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN notification_preferences JSONB 
                    DEFAULT '{"email_notifications": true, "email_on_job_completion": true, "email_on_job_failure": true, "notification_frequency": "immediate"}'
                """))
                
            # Check if event_metadata column exists with the right type
            if "event_metadata" not in audit_columns:
                logger.info("Adding event_metadata column to audit_logs table")
                await conn.execute(text("""
                    ALTER TABLE audit_logs 
                    ADD COLUMN event_metadata JSONB
                """))
                
            # Make sure we don't have any columns with reserved names
            if "metadata" in audit_columns:
                logger.info("Renaming metadata column to event_metadata in audit_logs table")
                # First check if event_metadata already exists to avoid duplicates
                if "event_metadata" not in audit_columns:
                    await conn.execute(text("""
                        ALTER TABLE audit_logs 
                        RENAME COLUMN metadata TO event_metadata
                    """))
                else:
                    # If both columns exist, migrate data and drop the old column
                    await conn.execute(text("""
                        UPDATE audit_logs 
                        SET event_metadata = metadata 
                        WHERE event_metadata IS NULL AND metadata IS NOT NULL
                    """))
                    await conn.execute(text("""
                        ALTER TABLE audit_logs 
                        DROP COLUMN metadata
                    """))
    
    logger.info("Schema verification complete")
    
if __name__ == "__main__":
    asyncio.run(ensure_schema()) 