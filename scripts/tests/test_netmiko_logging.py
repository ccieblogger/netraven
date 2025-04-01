#!/usr/bin/env python3
"""
Test script for Netmiko session logging in NetRaven.

This script tests the enhanced job logging functionality to ensure all required
job log entries are created:
1. Job Started with device details
2. Connecting to device with specific details
3. Session logs (or fallback if none available)
4. Success/failure result
5. Job ending entry

Usage:
    python scripts/test_netmiko_logging.py --host 192.168.1.1 --username admin --password cisco
"""

import os
import sys
import time
import uuid
import json
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the Python path so we can import netraven modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import NetRaven modules
from netraven.jobs.device_connector import JobDeviceConnector
from netraven.jobs.device_logging import start_job_session, end_job_session
from netraven.core.logging import get_logger

# Configure logging
logger = get_logger("netraven.test.netmiko_logging")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test NetRaven Netmiko session logging.")
    parser.add_argument("--host", required=True, help="Device hostname or IP address")
    parser.add_argument("--username", default="admin", help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument("--device-type", default=None, help="Device type (e.g., cisco_ios)")
    parser.add_argument("--port", type=int, default=22, help="SSH port (default: 22)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000", help="NetRaven API URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()

def get_auth_token(api_url: str) -> Optional[str]:
    """Get authentication token from the API."""
    login_data = {
        "username": "admin",
        "password": "NetRaven"
    }
    
    try:
        response = requests.post(f"{api_url}/api/auth/token", json=login_data)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            logger.error(f"Failed to get auth token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting auth token: {str(e)}")
        return None

def verify_job_logs(api_url: str, job_id: str, token: str) -> bool:
    """
    Verify that the job logs contain all required entries.
    
    Args:
        api_url: NetRaven API URL
        job_id: Job ID to check
        token: Authentication token
        
    Returns:
        bool: True if all required log entries are present, False otherwise
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Get the job log
    response = requests.get(f"{api_url}/api/job-logs/{job_id}", headers=headers)
    if response.status_code != 200:
        logger.error(f"Failed to get job log: {response.status_code} - {response.text}")
        return False
    
    job_log = response.json()
    job_log_id = job_log.get("id")
    
    # Get job log entries
    sub_response = requests.get(f"{api_url}/api/job-logs/{job_log_id}/entries", headers=headers)
    if sub_response.status_code != 200:
        logger.error(f"Failed to get job log entries: {sub_response.status_code} - {sub_response.text}")
        return False
    
    entries = sub_response.json()
    logger.info(f"Found {len(entries)} job log entries")
    
    # Verify required entry types
    has_job_started = False
    has_device_connection = False
    has_session_log = False
    has_connection_result = False
    has_job_ended = False
    
    # Print all entries for inspection
    for i, entry in enumerate(entries):
        logger.info(f"Entry {i+1}: [{entry.get('level')}] {entry.get('category')} - {entry.get('message')}")
        
        # Check categories
        category = entry.get("category")
        message = entry.get("message", "")
        
        if category == "job_started" or "Job started" in message:
            has_job_started = True
            
        if category == "device_connection" or "Connecting to" in message:
            has_device_connection = True
            
        if category == "session_log" or "session log" in message.lower():
            has_session_log = True
            
        if category == "connection_result" or (("failed" in message.lower() or "success" in message.lower()) and "connect" in message.lower()):
            has_connection_result = True
            
        if category == "job_ended" or "Job ended" in message:
            has_job_ended = True
    
    # Check if all required entries are present
    all_entries_present = has_job_started and has_device_connection and has_session_log and has_connection_result and has_job_ended
    
    if all_entries_present:
        logger.info("✅ All required job log entries are present!")
    else:
        logger.error("❌ Missing required job log entries:")
        if not has_job_started:
            logger.error("  - Missing job started entry")
        if not has_device_connection:
            logger.error("  - Missing device connection entry")
        if not has_session_log:
            logger.error("  - Missing session log entry")
        if not has_connection_result:
            logger.error("  - Missing connection result entry")
        if not has_job_ended:
            logger.error("  - Missing job ended entry")
    
    return all_entries_present

def main():
    """Main function."""
    args = parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger("netraven").setLevel(logging.DEBUG)
    
    logger.info(f"Testing Netmiko session logging to device {args.host}")
    
    # Start a job session
    session_id = start_job_session(description="Netmiko Logging Test")
    logger.info(f"Started job session: {session_id}")
    
    # Create a device ID for the test
    device_id = str(uuid.uuid4())
    logger.info(f"Using device ID: {device_id}")
    
    # Create a device connector
    device = JobDeviceConnector(
        device_id=device_id,
        host=args.host,
        username=args.username,
        password=args.password,
        device_type=args.device_type,
        port=args.port,
        session_id=session_id,
    )
    
    logger.info("Connecting to device...")
    
    # Connect to the device
    connected = device.connect()
    
    if connected:
        logger.info("Successfully connected to device")
        
        # Execute a simple command if connected
        logger.info("Executing simple command...")
        result = device.execute_command("show version")
        
        # Display results
        if result:
            logger.info(f"Command output: {result[:100]}...")
        else:
            logger.warning("No command output received")
        
        # Disconnect
        logger.info("Disconnecting from device...")
        device.disconnect()
    else:
        logger.error(f"Failed to connect to device: {device.last_error}")
    
    # End the job session
    end_job_session(session_id=session_id, success=connected)
    logger.info(f"Ended job session: {session_id}")
    
    # Wait a moment for job logs to be finalized
    logger.info("Waiting for job logs to be processed...")
    time.sleep(2)
    
    # Get auth token
    logger.info(f"Getting authentication token from {args.api_url}...")
    token = get_auth_token(args.api_url)
    
    if token:
        # Verify job logs
        logger.info(f"Verifying job logs for session {session_id}...")
        success = verify_job_logs(args.api_url, session_id, token)
        
        if success:
            logger.info("Test completed successfully - all required job log entries are present")
            sys.exit(0)
        else:
            logger.error("Test failed - missing required job log entries")
            sys.exit(1)
    else:
        logger.error("Test failed - could not get authentication token")
        sys.exit(1)

if __name__ == "__main__":
    main() 