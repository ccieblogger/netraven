#!/usr/bin/env python3

"""
Example script demonstrating the usage of DeviceConnector class.
This script connects to a network device and retrieves its configuration and information.
"""

import argparse
from pathlib import Path
from typing import Optional
import uuid

from utils.device_comm import DeviceConnector
from utils.log_util import get_logger
from utils.config import load_config, get_backup_path, commit_backup

# Generate a unique session ID
session_id = str(uuid.uuid4())

# Initialize logger with settings from config file
logger = get_logger("device_test")
logger.info(f"Device test script started - Session ID: {session_id}")  # Test log message

def connect_to_device(
    host: str,
    username: str,
    password: Optional[str] = None,
    device_type: Optional[str] = None,
    use_keys: bool = False,
    key_file: Optional[str] = None,
    port: int = 22,
    config_file: Optional[str] = None
) -> None:
    """
    Connect to a device and retrieve its information.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication (optional if using keys)
        device_type: Netmiko device type (auto-detected if not specified)
        use_keys: Whether to use SSH key authentication
        key_file: Path to SSH private key file
        port: SSH port number
        config_file: Path to configuration file (optional)
    """
    try:
        # Load configuration and get storage backend
        config, storage = load_config(config_file)
        
        # Create DeviceConnector instance
        device = DeviceConnector(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file
        )
        
        logger.debug(f"[Session: {session_id}] Attempting to connect to device {host}")
        
        # Use context manager for automatic connection handling
        with device:
            if device.is_connected:
                logger.debug(f"[Session: {session_id}] Successfully established connection to {host}")
                
                # Get device information
                os_info = device.get_os()
                if os_info:
                    logger.info(f"[Session: {session_id}] OS Information: {os_info}")
                
                serial = device.get_serial()
                if serial:
                    logger.info(f"[Session: {session_id}] Serial Number: {serial}")
                
                # Get running configuration
                config_text = device.get_running()
                if config_text:
                    logger.info(f"[Session: {session_id}] Retrieved running configuration")
                    # Get backup path and save configuration
                    backup_path = get_backup_path(host, config)
                    if storage.write_file(config_text, backup_path):
                        logger.info(f"[Session: {session_id}] Saved configuration to {backup_path}")
                        # Commit and push to Git if enabled (local storage only)
                        commit_backup(host, backup_path, config)
                    else:
                        logger.error(f"[Session: {session_id}] Failed to save configuration to {backup_path}")
            else:
                logger.error(f"[Session: {session_id}] Failed to connect to {host}")
            
            # Log disconnection (this will be executed when exiting the context manager)
            logger.info(f"[Session: {session_id}] Disconnected from {host}")
    
    except Exception as e:
        logger.error(f"[Session: {session_id}] Error occurred: {str(e)}", exc_info=True)

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Connect to a network device and retrieve its configuration."
    )
    parser.add_argument("host", help="Device hostname or IP address")
    parser.add_argument("username", help="Username for authentication")
    parser.add_argument(
        "--password",
        help="Password for authentication (optional if using keys)"
    )
    parser.add_argument(
        "--device-type",
        help="Netmiko device type (auto-detected if not specified)"
    )
    parser.add_argument(
        "--use-keys",
        action="store_true",
        help="Use SSH key authentication"
    )
    parser.add_argument(
        "--key-file",
        help="Path to SSH private key file"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=22,
        help="SSH port number (default: 22)"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Validate SSH key arguments
    if args.use_keys and not args.key_file:
        parser.error("--key-file is required when using SSH key authentication")
    
    if not args.use_keys and not args.password:
        parser.error("Either --password or --use-keys with --key-file is required")
    
    connect_to_device(
        host=args.host,
        username=args.username,
        password=args.password,
        device_type=args.device_type,
        use_keys=args.use_keys,
        key_file=args.key_file,
        port=args.port,
        config_file=args.config
    )

if __name__ == "__main__":
    main() 