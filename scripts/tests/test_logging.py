#!/usr/bin/env python3
"""
Test script for demonstrating the enhanced logging functionality.

This script generates sample log messages for various components to demonstrate
how they are directed to component-specific log files.
"""

import os
import sys
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from netraven.core.logging import get_logger
from netraven.core.config import load_config, get_default_config_path

def ensure_log_directory():
    """Ensure the logs directory exists with proper permissions."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Give write permissions for all users to the logs directory
    os.chmod(log_dir, 0o777)
    
    # Create placeholder files with correct permissions
    components = ["frontend", "backend", "jobs", "auth"]
    for component in components:
        log_file = os.path.join(log_dir, f"{component}.log")
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("")
            os.chmod(log_file, 0o666)

def test_logging():
    """Test the enhanced logging functionality."""
    # Ensure logs directory exists with proper permissions
    ensure_log_directory()
    
    # Create a unique session ID for this test run
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Testing enhanced logging functionality at {timestamp}")
    print(f"Session ID: {session_id}")
    print("Generating log messages for different components...")
    
    # Load configuration
    config_path = os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
    config, _ = load_config(config_path)
    
    # Create loggers for different components
    frontend_logger = get_logger("netraven.frontend")
    backend_logger = get_logger("netraven.web.backend")
    api_logger = get_logger("netraven.web.api")
    auth_logger = get_logger("netraven.web.routers.auth")
    jobs_logger = get_logger("netraven.jobs.scheduler")
    
    # Generate frontend logs
    print("\nGenerating frontend logs...")
    frontend_logger.info(f"[Session: {session_id}] Frontend application started")
    frontend_logger.debug(f"[Session: {session_id}] Initializing Vue.js components")
    frontend_logger.warning(f"[Session: {session_id}] Browser compatibility issue detected")
    frontend_logger.error(f"[Session: {session_id}] Failed to load resource: assets/image.png")
    
    # Generate backend logs
    print("\nGenerating backend logs...")
    backend_logger.info(f"[Session: {session_id}] Backend API server started")
    backend_logger.debug(f"[Session: {session_id}] Database connection established")
    backend_logger.warning(f"[Session: {session_id}] Slow database query detected")
    
    # Generate API logs (should go to backend log)
    print("\nGenerating API logs...")
    api_logger.info(f"[Session: {session_id}] API request: GET /api/devices")
    api_logger.debug(f"[Session: {session_id}] API response: 200 OK, returned 5 devices")
    api_logger.warning(f"[Session: {session_id}] Rate limit approaching for client 192.168.1.10")
    
    # Generate authentication logs
    print("\nGenerating authentication logs...")
    auth_logger.info(f"[Session: {session_id}] User 'admin' logged in successfully")
    auth_logger.debug(f"[Session: {session_id}] JWT token generated with expiry: 1 hour")
    auth_logger.warning(f"[Session: {session_id}] Failed login attempt for user 'unknown'")
    auth_logger.error(f"[Session: {session_id}] Authentication token revoked due to suspicious activity")
    
    # Generate job logs
    print("\nGenerating job logs...")
    jobs_logger.info(f"[Session: {session_id}] Backup job started for 5 devices")
    jobs_logger.debug(f"[Session: {session_id}] Device 'router1' backup initiated")
    jobs_logger.warning(f"[Session: {session_id}] Device 'switch3' not responding, retry #1")
    jobs_logger.error(f"[Session: {session_id}] Device 'firewall2' backup failed after 3 retries")
    
    # Show log file locations
    log_dir = config["logging"]["directory"]
    print("\nLog files have been created in the following locations:")
    print(f"- Main log: {log_dir}/{config['logging']['filename']}")
    for component, filename in config["logging"]["components"]["files"].items():
        print(f"- {component.capitalize()} log: {log_dir}/{filename}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_logging() 