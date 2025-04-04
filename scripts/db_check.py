#!/usr/bin/env python3
"""
Database connection checker for NetRaven.

This utility script tests the database connection and provides
information about the database configuration and schema.
"""

import os
import sys
from pathlib import Path
import argparse
import time

# Add the parent directory to the path so we can import netraven
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Import required modules
from sqlalchemy import inspect, text
from netraven.web.database import engine, init_db
from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger

# Create logger
logger = get_logger("netraven.scripts.db_check")

def check_database_connection(retries=5, retry_interval=2):
    """
    Check if the database is accessible.
    
    Args:
        retries: Number of times to retry connection
        retry_interval: Seconds between retries
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    for attempt in range(retries):
        try:
            # Try to execute a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
    
    logger.error("Failed to connect to database after several attempts")
    return False

def list_tables():
    """List all tables in the database."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    if not table_names:
        logger.info("No tables found in database")
        return
    
    logger.info(f"Found {len(table_names)} tables:")
    for table in table_names:
        logger.info(f"  - {table}")
        # Get column information
        columns = inspector.get_columns(table)
        for column in columns:
            logger.info(f"      {column['name']} ({column['type']})")

def show_database_info():
    """Show information about the database configuration."""
    # Load configuration
    config, _ = load_config(get_default_config_path())
    db_config = config["web"]["database"]
    
    logger.info(f"Database type: {db_config['type']}")
    if db_config['type'] == 'sqlite':
        logger.info(f"Database path: {db_config['sqlite']['path']}")
    elif db_config['type'] == 'postgres':
        pg_config = db_config['postgres']
        # Don't log the password
        logger.info(f"PostgreSQL host: {pg_config['host']}:{pg_config['port']}")
        logger.info(f"PostgreSQL database: {pg_config['database']}")
        logger.info(f"PostgreSQL user: {pg_config['user']}")
    
    logger.info(f"SQLAlchemy URL: {engine.url}")
    
    return db_config

def verify_postgres_only():
    """
    Verify that the configuration is set to use PostgreSQL only.
    
    Returns:
        bool: True if PostgreSQL is configured, False if another database type is configured
    """
    config, _ = load_config(get_default_config_path())
    db_config = config["web"]["database"]
    
    if db_config['type'] != 'postgres':
        logger.error(f"Invalid database type: {db_config['type']}. NetRaven only supports PostgreSQL.")
        return False
    
    # Check if essential PostgreSQL configuration is present
    pg_config = db_config.get('postgres', {})
    missing_config = []
    for required in ['host', 'port', 'database', 'user', 'password']:
        if not pg_config.get(required):
            missing_config.append(required)
    
    if missing_config:
        logger.error(f"Missing required PostgreSQL configuration: {', '.join(missing_config)}")
        return False
    
    logger.info("PostgreSQL configuration verified")
    return True

def check_required_tables():
    """
    Check if all required tables exist in the database.
    
    Returns:
        bool: True if all required tables exist, False otherwise
    """
    required_tables = [
        "users", "devices", "tags", "credentials", "credential_tags",
        "backups", "job_logs", "job_log_entries", "scheduled_jobs", 
        "admin_settings", "audit_logs"
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    missing_tables = [t for t in required_tables if t not in existing_tables]
    
    if missing_tables:
        logger.error(f"Missing required tables: {', '.join(missing_tables)}")
        return False
    
    logger.info("All required tables exist")
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Check database connection and configuration"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema"
    )
    parser.add_argument(
        "--postgres-only",
        action="store_true",
        help="Verify that PostgreSQL is the only database configured and fail if any SQLite configuration is found"
    )
    parser.add_argument(
        "--check-tables",
        action="store_true",
        help="Check if all required tables exist in the database"
    )
    
    args = parser.parse_args()
    
    # Show database configuration
    db_config = show_database_info()
    
    # Verify PostgreSQL-only configuration if requested
    if args.postgres_only and not verify_postgres_only():
        logger.error("PostgreSQL-only check failed - exiting")
        return 1
    
    # Check database connection
    if not check_database_connection():
        return 1
    
    # Check required tables if requested
    if args.check_tables and not check_required_tables():
        return 1
    
    # Initialize database if requested
    if args.init:
        try:
            logger.info("Initializing database schema...")
            init_db()
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return 1
    
    # List tables
    list_tables()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 