#!/usr/bin/env python3
"""
Script to migrate logs from files to the database.

This script reads log files and migrates their contents to the database,
organizing them by session ID and creating appropriate job logs and entries.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from netraven.core.config import load_config, get_default_config_path
from netraven.core.db_logging import migrate_logs_to_database

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("migrate_logs")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Migrate logs from files to the database")
    parser.add_argument("--config", help="Path to configuration file", default=get_default_config_path())
    parser.add_argument("--log-dir", help="Directory containing log files", default=None)
    parser.add_argument("--log-file", help="Specific log file to migrate", default=None)
    parser.add_argument("--job-type", help="Job type to assign to migrated logs", default="legacy")
    parser.add_argument("--user-id", help="User ID to assign to migrated logs", default="system")
    parser.add_argument("--dry-run", help="Don't actually migrate logs, just show what would be done", action="store_true")
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Load configuration
    config, _ = load_config(args.config)
    
    # Get log directory from config if not specified
    log_dir = args.log_dir or config["logging"]["directory"]
    log_dir_path = Path(log_dir)
    
    if not log_dir_path.exists():
        logger.error(f"Log directory {log_dir_path} does not exist")
        return 1
    
    # Get log files to migrate
    log_files = []
    if args.log_file:
        log_file_path = Path(args.log_file)
        if not log_file_path.exists():
            logger.error(f"Log file {log_file_path} does not exist")
            return 1
        log_files.append(log_file_path)
    else:
        # Get all log files in the directory
        log_files = list(log_dir_path.glob("*.log"))
    
    if not log_files:
        logger.warning(f"No log files found in {log_dir_path}")
        return 0
    
    # Migrate each log file
    total_entries = 0
    for log_file in log_files:
        logger.info(f"Migrating log file: {log_file}")
        
        if args.dry_run:
            logger.info(f"Dry run: would migrate {log_file}")
            continue
        
        # Determine job type based on file name
        job_type = args.job_type
        if log_file.name == "jobs.log":
            job_type = "device_backup"
        elif log_file.name == "auth.log":
            job_type = "authentication"
        elif log_file.name == "backend.log":
            job_type = "api"
        
        # Migrate the log file
        entries = migrate_logs_to_database(str(log_file), job_type, args.user_id)
        total_entries += entries
        
        logger.info(f"Migrated {entries} entries from {log_file}")
    
    logger.info(f"Migration complete: {total_entries} entries migrated from {len(log_files)} files")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 