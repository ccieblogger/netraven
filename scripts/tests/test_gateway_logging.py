#!/usr/bin/env python3
"""
Test script for the Device Gateway logging integration.

This script tests the integration of the gateway service with the
enhanced logging system, including database logging.
"""

import sys
import os
import argparse
import json
import time
import requests
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.gateway.client import GatewayClient
from netraven.web.database import SessionLocal
from netraven.web.models.job_log import JobLog, JobLogEntry

def test_gateway_logging(gateway_url: str, api_key: str) -> bool:
    """
    Test the gateway logging integration.
    
    Args:
        gateway_url: URL of the gateway API
        api_key: API key for authentication
        
    Returns:
        True if the test passed, False otherwise
    """
    print(f"\n=== Testing gateway logging integration ===")
    
    # Create a gateway client
    client = GatewayClient(
        gateway_url=gateway_url,
        api_key=api_key,
        client_id="test-client"
    )
    
    # Test health check
    try:
        health = client.check_health()
        print(f"Health check successful: {health}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test device connection (will fail but should generate logs)
    try:
        result = client.connect_device(
            host="test-device.local",
            username="test",
            password="test"
        )
        print(f"Connection result: {result}")
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    # Wait for logs to be written
    print("Waiting for logs to be written...")
    time.sleep(2)
    
    # Check database for logs
    return check_database_logs()

def check_database_logs() -> bool:
    """
    Check the database for gateway logs.
    
    Returns:
        True if logs were found, False otherwise
    """
    print("\n=== Checking database for gateway logs ===")
    
    try:
        # Connect to database
        db = SessionLocal()
        
        try:
            # Query for gateway job logs
            job_logs = db.query(JobLog).filter(JobLog.job_type == "gateway_operation").all()
            
            if not job_logs:
                print("No gateway job logs found in database")
                return False
            
            print(f"Found {len(job_logs)} gateway job logs:")
            for log in job_logs:
                print(f"  - ID: {log.id}")
                print(f"    Session: {log.session_id}")
                print(f"    Status: {log.status}")
                print(f"    Start time: {log.start_time}")
                print(f"    End time: {log.end_time}")
                print(f"    Result: {log.result_message}")
                
                # Query for log entries
                entries = db.query(JobLogEntry).filter(JobLogEntry.job_log_id == log.id).all()
                print(f"    Entries: {len(entries)}")
                
                # Print a sample of entries
                if entries:
                    print("\n    Sample log entries:")
                    for entry in entries[:5]:  # Show first 5 entries
                        print(f"      {entry.timestamp} - {entry.level} - {entry.message}")
                    
                    if len(entries) > 5:
                        print(f"      ... and {len(entries) - 5} more entries")
            
            return True
        finally:
            db.close()
    except Exception as e:
        print(f"Error checking database logs: {e}")
        return False

def check_log_files() -> bool:
    """
    Check log files for gateway logs.
    
    Returns:
        True if logs were found, False otherwise
    """
    print("\n=== Checking log files for gateway logs ===")
    
    # Define log files to check
    log_files = [
        "logs/netraven.log",
        "logs/gateway.log"
    ]
    
    found_logs = False
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"Checking {log_file}...")
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    
                    # Look for gateway logs
                    gateway_lines = [line for line in lines if "netraven.gateway" in line]
                    
                    if gateway_lines:
                        print(f"Found {len(gateway_lines)} gateway log lines in {log_file}")
                        print("\nSample log lines:")
                        for line in gateway_lines[-5:]:  # Show last 5 lines
                            print(f"  {line.strip()}")
                        
                        found_logs = True
                    else:
                        print(f"No gateway logs found in {log_file}")
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        else:
            print(f"Log file {log_file} does not exist")
    
    return found_logs

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the Device Gateway logging integration")
    parser.add_argument("--url", default="http://localhost:8001", help="URL of the gateway API")
    parser.add_argument("--api-key", default="netraven-api-key", help="API key for authentication")
    args = parser.parse_args()
    
    # Test gateway logging
    gateway_logging_passed = test_gateway_logging(args.url, args.api_key)
    
    # Check log files
    log_files_passed = check_log_files()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Gateway logging integration: {'PASSED' if gateway_logging_passed else 'FAILED'}")
    print(f"Log files check: {'PASSED' if log_files_passed else 'FAILED'}")
    
    # Return success if both tests passed
    return 0 if gateway_logging_passed and log_files_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 