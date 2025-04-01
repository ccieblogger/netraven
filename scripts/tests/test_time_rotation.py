#!/usr/bin/env python3
"""
Test script for demonstrating time-based log rotation.

This script modifies the logging configuration to use time-based rotation
and generates sample log messages to demonstrate the functionality.
"""

import os
import sys
import time
import yaml
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from netraven.core.logging import get_logger, configure_logging
from netraven.core.config import load_config, get_default_config_path

def setup_time_based_rotation():
    """Configure time-based log rotation settings."""
    # Load the config
    config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Enable time-based rotation for testing (every minute)
    config['logging']['file']['rotation_when'] = 'M'  # Every minute for demo purposes
    config['logging']['file']['rotation_interval'] = 1
    
    config['logging']['json']['enabled'] = True
    config['logging']['json']['rotation_when'] = 'M'
    config['logging']['json']['rotation_interval'] = 1
    
    config['logging']['components']['rotation_when'] = 'M'
    config['logging']['components']['rotation_interval'] = 1
    
    # Apply the configuration
    configure_logging(config)
    
    print(f"Configured time-based log rotation (every minute)")
    
    return config

def generate_logs(duration_seconds=180):
    """
    Generate log messages over the specified duration.
    
    Args:
        duration_seconds: How long to generate logs for, in seconds
    """
    # Create loggers for different components
    main_logger = get_logger("netraven.main")
    frontend_logger = get_logger("netraven.frontend")
    backend_logger = get_logger("netraven.web.backend")
    auth_logger = get_logger("netraven.web.routers.auth")
    jobs_logger = get_logger("netraven.jobs.scheduler")
    
    print(f"Generating logs for {duration_seconds} seconds (watch for rotation)...")
    
    start_time = time.time()
    log_count = 0
    
    while time.time() - start_time < duration_seconds:
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Log to all loggers
        main_logger.info(f"[{timestamp}] Main application log #{log_count}")
        frontend_logger.info(f"[{timestamp}] Frontend application log #{log_count}")
        backend_logger.info(f"[{timestamp}] Backend API server log #{log_count}")
        auth_logger.info(f"[{timestamp}] Auth system log #{log_count}")
        jobs_logger.info(f"[{timestamp}] Job scheduler log #{log_count}")
        
        # Sleep a bit to avoid flooding logs
        time.sleep(1)
        log_count += 1
        
        # Print progress every 10 seconds
        elapsed = time.time() - start_time
        if elapsed % 10 < 1:
            remaining = duration_seconds - elapsed
            print(f"Elapsed: {int(elapsed)}s, Remaining: {int(remaining)}s, Logs generated: {log_count}")
    
    print(f"Log generation complete. Generated {log_count} logs.")

def check_rotated_logs(config):
    """Check for the existence of rotated log files."""
    log_dir = config['logging']['directory']
    print("\nChecking for rotated log files:")
    
    # Get all files in log directory
    log_files = os.listdir(log_dir)
    rotated_files = [f for f in log_files if '.' in f and f.split('.')[-1].isdigit()]
    
    if rotated_files:
        print(f"Found {len(rotated_files)} rotated log files:")
        for file in sorted(rotated_files):
            file_path = os.path.join(log_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file} ({file_size} bytes)")
    else:
        print("No rotated log files found. The rotation period may not have triggered yet.")
    
    return len(rotated_files) > 0

def main():
    """Main function to test time-based log rotation."""
    print("Testing time-based log rotation")
    print("=" * 60)
    
    # Configure time-based rotation
    config = setup_time_based_rotation()
    
    # Generate logs for a period of time (3 minutes by default)
    # This should trigger at least 3 rotations
    generate_logs(duration_seconds=180)
    
    # Check for rotated log files
    rotated = check_rotated_logs(config)
    
    if rotated:
        print("\nSuccess! Time-based log rotation is working correctly.")
    else:
        print("\nLog files don't appear to have rotated. Possible issues:")
        print("1. The rotation interval wasn't long enough")
        print("2. There might be an issue with the implementation")
        print("3. The log directory may not have the correct permissions")
    
    print("\nTest complete.\n")

if __name__ == "__main__":
    main() 