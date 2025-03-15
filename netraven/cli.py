#!/usr/bin/env python3
"""
Command-line interface for NetRaven.

This module provides the main entry point for the NetRaven CLI tool,
which can be used to trigger backups, manage configurations, and
launch the web interface.
"""

import argparse
import sys
import os
from pathlib import Path
import shutil
import subprocess
import logging
import yaml
from typing import Optional, List, Dict, Any

# Import internal modules
from netraven.core.config import (
    load_config, 
    get_default_config_path,
    DEFAULT_CONFIG
)
from netraven.core.logging import get_logger
from netraven.core.device_comm import backup_device_config

def setup_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="NetRaven - Network Configuration Backup Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=str(get_default_config_path())
    )
    parser.add_argument(
        "--verbose", "-v",
        help="Increase verbosity",
        action="count",
        default=0
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Backup command
    backup_parser = subparsers.add_parser(
        "backup",
        help="Backup device configurations"
    )
    backup_parser.add_argument(
        "device",
        nargs="*",
        help="Device hostnames or IP addresses to back up"
    )
    backup_parser.add_argument(
        "--all",
        help="Backup all devices from inventory",
        action="store_true"
    )
    backup_parser.add_argument(
        "--type",
        help="Device type (cisco_ios, juniper_junos, etc.)",
        default=None
    )
    
    # Schedule command
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Schedule backup jobs"
    )
    schedule_subparsers = schedule_parser.add_subparsers(
        dest="schedule_command",
        help="Schedule command to execute"
    )
    
    # Schedule add command
    schedule_add_parser = schedule_subparsers.add_parser(
        "add",
        help="Add a scheduled backup job"
    )
    schedule_add_parser.add_argument(
        "device",
        help="Device hostname or IP address to back up"
    )
    schedule_add_parser.add_argument(
        "--device-id",
        help="Device ID (defaults to hostname)",
        default=None
    )
    schedule_add_parser.add_argument(
        "--type",
        help="Device type (cisco_ios, juniper_junos, etc.)",
        default=None
    )
    schedule_add_parser.add_argument(
        "--schedule-type",
        help="Schedule type (daily, weekly, interval)",
        choices=["daily", "weekly", "interval"],
        default="daily"
    )
    schedule_add_parser.add_argument(
        "--time",
        help="Time for daily/weekly jobs (HH:MM format)",
        default="00:00"
    )
    schedule_add_parser.add_argument(
        "--interval",
        help="Interval in minutes for interval jobs",
        type=int,
        default=None
    )
    schedule_add_parser.add_argument(
        "--day",
        help="Day of week for weekly jobs",
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        default=None
    )
    schedule_add_parser.add_argument(
        "--name",
        help="Name for the scheduled job",
        default=None
    )
    
    # Schedule list command
    schedule_list_parser = schedule_subparsers.add_parser(
        "list",
        help="List scheduled backup jobs"
    )
    
    # Schedule remove command
    schedule_remove_parser = schedule_subparsers.add_parser(
        "remove",
        help="Remove a scheduled backup job"
    )
    schedule_remove_parser.add_argument(
        "job_id",
        help="ID of the job to remove"
    )
    
    # Web server command
    web_parser = subparsers.add_parser(
        "web",
        help="Start the web interface"
    )
    web_parser.add_argument(
        "--host",
        help="Host to bind the web server to",
        default=None
    )
    web_parser.add_argument(
        "--port",
        help="Port to bind the web server to",
        type=int,
        default=None
    )
    web_parser.add_argument(
        "--reload",
        help="Enable auto-reload for development",
        action="store_true"
    )
    
    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize NetRaven configuration"
    )
    init_parser.add_argument(
        "--force",
        help="Overwrite existing configuration",
        action="store_true"
    )
    
    # Version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information"
    )
    
    return parser

def backup_command(args: argparse.Namespace, config: Dict[str, Any], logger: logging.Logger) -> int:
    """
    Execute the backup command.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        int: Exit code (0 on success)
    """
    if not args.device and not args.all:
        logger.error("No devices specified and --all not provided")
        return 1
    
    success_count = 0
    failure_count = 0
    
    # TODO: Implement inventory loading when --all is specified
    
    for device in args.device:
        try:
            logger.info(f"Backing up device {device}")
            # For now, we'll just use default credentials from environment variables
            username = os.environ.get("NETRAVEN_USERNAME", "")
            password = os.environ.get("NETRAVEN_PASSWORD", "")
            
            if not username or not password:
                logger.error("No credentials provided. Set NETRAVEN_USERNAME and NETRAVEN_PASSWORD environment variables")
                return 1
                
            result = backup_device_config(
                host=device,
                username=username,
                password=password,
                device_type=args.type,
                config=config
            )
            
            if result:
                logger.info(f"Successfully backed up {device}")
                success_count += 1
            else:
                logger.error(f"Failed to back up {device}")
                failure_count += 1
                
        except Exception as e:
            logger.exception(f"Error backing up {device}: {e}")
            failure_count += 1
    
    logger.info(f"Backup completed: {success_count} successful, {failure_count} failed")
    return 0 if failure_count == 0 else 1

def web_command(args: argparse.Namespace, config: Dict[str, Any], logger: logging.Logger) -> int:
    """
    Start the web interface.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        int: Exit code (0 on success)
    """
    try:
        from netraven.web import app
        import uvicorn
        
        # Use command-line arguments if provided, otherwise use configuration
        host = args.host or config['web']['host']
        port = args.port or config['web']['port']
        
        logger.info(f"Starting web interface on {host}:{port}")
        
        # Start the web server
        uvicorn.run(
            "netraven.web:app",
            host=host,
            port=port,
            reload=args.reload,
            log_level="info"
        )
        
        return 0
    except ImportError:
        logger.error("Web dependencies not installed. Please install with 'pip install netraven[web]'")
        return 1
    except Exception as e:
        logger.exception(f"Error starting web interface: {e}")
        return 1

def init_command(args: argparse.Namespace, logger: logging.Logger) -> int:
    """
    Initialize NetRaven configuration.
    
    Args:
        args: Command-line arguments
        logger: Logger instance
        
    Returns:
        int: Exit code (0 on success)
    """
    config_path = get_default_config_path()
    
    if os.path.exists(config_path) and not args.force:
        logger.warning(f"Configuration file already exists at {config_path}")
        logger.warning("Use --force to overwrite")
        return 1
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Write default config to file
        with open(config_path, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
            
        logger.info(f"Created configuration file at {config_path}")
        
        # Create logs directory
        logs_dir = os.path.join(os.path.dirname(config_path), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        logger.info(f"Created logs directory at {logs_dir}")
        
        # Create data directory
        data_dir = os.path.join(os.path.dirname(config_path), "data")
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Created data directory at {data_dir}")
        
        # Create backups directory
        backups_dir = os.path.join(data_dir, "backups")
        os.makedirs(backups_dir, exist_ok=True)
        logger.info(f"Created backups directory at {backups_dir}")
        
        return 0
    except Exception as e:
        logger.exception(f"Error initializing configuration: {e}")
        return 1

def version_command(logger: logging.Logger) -> int:
    """
    Show version information.
    
    Args:
        logger: Logger instance
        
    Returns:
        int: Exit code (0 on success)
    """
    import pkg_resources
    
    try:
        version = pkg_resources.get_distribution("netraven").version
        logger.info(f"NetRaven version {version}")
        return 0
    except Exception as e:
        logger.exception(f"Error getting version information: {e}")
        return 1

def schedule_command(args: argparse.Namespace, config: Dict[str, Any], logger: logging.Logger) -> int:
    """
    Execute the schedule command.
    
    Args:
        args: Command-line arguments
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        int: Exit code (0 on success)
    """
    try:
        from netraven.jobs.scheduler import get_scheduler
        
        # Get scheduler instance
        scheduler = get_scheduler(args.config)
        
        if args.schedule_command == "add":
            # Get credentials
            username = os.environ.get("NETRAVEN_USERNAME", "")
            password = os.environ.get("NETRAVEN_PASSWORD", "")
            
            if not username or not password:
                logger.error("No credentials provided. Set NETRAVEN_USERNAME and NETRAVEN_PASSWORD environment variables")
                return 1
            
            # Use hostname as device ID if not provided
            device_id = args.device_id or args.device
            
            # Validate schedule parameters
            if args.schedule_type == "weekly" and not args.day:
                logger.error("Day of week is required for weekly schedules")
                return 1
            if args.schedule_type == "interval" and not args.interval:
                logger.error("Interval is required for interval schedules")
                return 1
            
            # Schedule the backup job
            job_id = scheduler.schedule_backup(
                device_id=device_id,
                host=args.device,
                username=username,
                password=password,
                device_type=args.type,
                schedule_type=args.schedule_type,
                schedule_time=args.time,
                schedule_interval=args.interval,
                schedule_day=args.day,
                job_name=args.name
            )
            
            logger.info(f"Scheduled backup job {job_id} for device {args.device}")
            
            # Start the scheduler if not already running
            if not scheduler.running:
                scheduler.start()
                
            return 0
            
        elif args.schedule_command == "list":
            # List scheduled jobs
            jobs = scheduler.list_jobs()
            
            if not jobs:
                logger.info("No scheduled backup jobs")
                return 0
                
            logger.info(f"Scheduled backup jobs ({len(jobs)}):")
            for job in jobs:
                if job["schedule_type"] == "daily":
                    schedule_info = f"daily at {job['schedule_time']}"
                elif job["schedule_type"] == "weekly":
                    schedule_info = f"weekly on {job['schedule_day']} at {job['schedule_time']}"
                elif job["schedule_type"] == "interval":
                    schedule_info = f"every {job['schedule_interval']} minutes"
                else:
                    schedule_info = "unknown schedule"
                    
                logger.info(f"  {job['id']}: {job['name']} - {schedule_info}")
                
            return 0
            
        elif args.schedule_command == "remove":
            # Remove scheduled job
            result = scheduler.cancel_job(args.job_id)
            
            if result:
                logger.info(f"Removed scheduled backup job {args.job_id}")
                return 0
            else:
                logger.error(f"Job {args.job_id} not found")
                return 1
                
        else:
            logger.error(f"Unknown schedule command: {args.schedule_command}")
            return 1
            
    except ImportError:
        logger.error("Scheduler module not available")
        return 1
    except Exception as e:
        logger.exception(f"Error executing schedule command: {e}")
        return 1

def main() -> int:
    """
    Main entry point for the NetRaven CLI.
    
    Returns:
        int: Exit code (0 on success)
    """
    parser = setup_parser()
    args = parser.parse_args()
    
    # Initialize logger
    logger = get_logger("netraven.cli")
    
    # Handle version command early
    if args.command == "version":
        return version_command(logger)
    
    # Handle init command (doesn't need config)
    if args.command == "init":
        return init_command(args, logger)
    
    # Load configuration
    try:
        config, storage = load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1
    
    # Execute command
    if args.command == "backup":
        return backup_command(args, config, logger)
    elif args.command == "web":
        return web_command(args, config, logger)
    elif args.command == "schedule":
        return schedule_command(args, config, logger)
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main()) 