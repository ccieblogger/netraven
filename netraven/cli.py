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
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main()) 