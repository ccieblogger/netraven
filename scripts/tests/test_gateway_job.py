#!/usr/bin/env python3
"""
Test script for gateway job integration.

This script tests the integration of the gateway service with the job scheduling system.
"""

import sys
import os
import argparse
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.jobs.gateway_connector import (
    check_device_connectivity_via_gateway,
    connect_device_via_gateway,
    execute_command_via_gateway,
    backup_device_config_via_gateway
)
from netraven.jobs.scheduler import get_scheduler
from netraven.web.database import SessionLocal
from netraven.web.models.job_log import JobLog, JobLogEntry

def test_gateway_connectivity(host: str) -> bool:
    """
    Test gateway connectivity to a device.
    
    Args:
        host: Device hostname or IP address
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing gateway connectivity to {host} ===")
    
    # Check connectivity
    reachable, error = check_device_connectivity_via_gateway(host)
    
    if reachable:
        print(f"Gateway connectivity check passed")
        return True
    else:
        print(f"Gateway connectivity check failed: {error}")
        return False

def test_gateway_connect(
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None
) -> bool:
    """
    Test connecting to a device via the gateway.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing device connection via gateway to {host} ===")
    
    # Generate a test device ID
    device_id = f"test-{int(time.time())}"
    
    # Connect to device
    connected, device_info = connect_device_via_gateway(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        device_type=device_type
    )
    
    if connected:
        print(f"Device connection successful")
        if device_info:
            print(f"Device info: {device_info}")
        return True
    else:
        print(f"Device connection failed")
        return False

def test_gateway_command(
    host: str,
    username: str,
    password: str,
    command: str = "get_os_info",
    device_type: Optional[str] = None
) -> bool:
    """
    Test executing a command on a device via the gateway.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        command: Command to execute
        device_type: Device type
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing command execution via gateway on {host} ===")
    print(f"Command: {command}")
    
    # Generate a test device ID
    device_id = f"test-{int(time.time())}"
    
    # Execute command
    success, result = execute_command_via_gateway(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        command=command,
        device_type=device_type
    )
    
    if success:
        print(f"Command execution successful")
        print(f"Result: {result}")
        return True
    else:
        print(f"Command execution failed")
        return False

def test_gateway_backup(
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None
) -> bool:
    """
    Test backing up a device configuration via the gateway.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing device backup via gateway for {host} ===")
    
    # Generate a test device ID
    device_id = f"test-{int(time.time())}"
    
    # Backup device
    success = backup_device_config_via_gateway(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        device_type=device_type
    )
    
    if success:
        print(f"Device backup successful")
        return True
    else:
        print(f"Device backup failed")
        return False

def test_scheduled_backup(
    host: str,
    username: str,
    password: str,
    device_type: Optional[str] = None
) -> bool:
    """
    Test scheduling a backup job via the gateway.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        device_type: Device type
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing scheduled backup via gateway for {host} ===")
    
    # Generate a test device ID
    device_id = f"test-{int(time.time())}"
    
    # Get scheduler
    scheduler = get_scheduler()
    
    # Schedule backup job
    job_id = scheduler.schedule_backup(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        device_type=device_type,
        schedule_type="interval",
        schedule_interval=60,  # 60 minutes
        job_name=f"Test backup for {host}",
        use_gateway=True
    )
    
    print(f"Scheduled backup job with ID: {job_id}")
    
    # Run the job immediately
    print("Running the job immediately...")
    success = scheduler.run_job_now(job_id)
    
    # Cancel the job
    scheduler.cancel_job(job_id)
    print(f"Cancelled job {job_id}")
    
    if success:
        print(f"Scheduled backup executed successfully")
        return True
    else:
        print(f"Scheduled backup execution failed")
        return False

def test_scheduled_command(
    host: str,
    username: str,
    password: str,
    command: str = "get_os_info",
    device_type: Optional[str] = None
) -> bool:
    """
    Test scheduling a command job via the gateway.
    
    Args:
        host: Device hostname or IP address
        username: Username for authentication
        password: Password for authentication
        command: Command to execute
        device_type: Device type
        
    Returns:
        bool: True if test passed, False otherwise
    """
    print(f"\n=== Testing scheduled command via gateway for {host} ===")
    print(f"Command: {command}")
    
    # Generate a test device ID
    device_id = f"test-{int(time.time())}"
    
    # Get scheduler
    scheduler = get_scheduler()
    
    # Schedule command job
    job_id = scheduler.schedule_command(
        device_id=device_id,
        host=host,
        username=username,
        password=password,
        command=command,
        device_type=device_type,
        schedule_type="interval",
        schedule_interval=60,  # 60 minutes
        job_name=f"Test command for {host}"
    )
    
    print(f"Scheduled command job with ID: {job_id}")
    
    # Run the job immediately
    print("Running the job immediately...")
    success = scheduler.run_job_now(job_id)
    
    # Cancel the job
    scheduler.cancel_job(job_id)
    print(f"Cancelled job {job_id}")
    
    if success:
        print(f"Scheduled command executed successfully")
        return True
    else:
        print(f"Scheduled command execution failed")
        return False

def check_job_logs() -> bool:
    """
    Check the database for gateway job logs.
    
    Returns:
        bool: True if logs were found, False otherwise
    """
    print("\n=== Checking database for gateway job logs ===")
    
    try:
        # Connect to database
        db = SessionLocal()
        
        try:
            # Query for gateway job logs
            job_logs = db.query(JobLog).filter(
                JobLog.job_type.in_([
                    "gateway_device_check",
                    "gateway_device_connect",
                    "gateway_device_command",
                    "gateway_device_backup"
                ])
            ).all()
            
            if not job_logs:
                print("No gateway job logs found in database")
                return False
            
            print(f"Found {len(job_logs)} gateway job logs:")
            for log in job_logs:
                print(f"  - ID: {log.id}")
                print(f"    Type: {log.job_type}")
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

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test gateway job integration")
    parser.add_argument("--host", required=True, help="Device hostname or IP address")
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument("--device-type", help="Device type (auto-detected if not provided)")
    parser.add_argument("--command", default="get_os_info", help="Command to execute")
    parser.add_argument("--skip-connect", action="store_true", help="Skip connection test")
    parser.add_argument("--skip-command", action="store_true", help="Skip command test")
    parser.add_argument("--skip-backup", action="store_true", help="Skip backup test")
    parser.add_argument("--skip-scheduled", action="store_true", help="Skip scheduled job tests")
    args = parser.parse_args()
    
    # Run tests
    tests = []
    
    # Test gateway connectivity
    connectivity_passed = test_gateway_connectivity(args.host)
    tests.append(("Gateway Connectivity", connectivity_passed))
    
    if not args.skip_connect:
        # Test device connection
        connect_passed = test_gateway_connect(
            host=args.host,
            username=args.username,
            password=args.password,
            device_type=args.device_type
        )
        tests.append(("Device Connection", connect_passed))
    
    if not args.skip_command:
        # Test command execution
        command_passed = test_gateway_command(
            host=args.host,
            username=args.username,
            password=args.password,
            command=args.command,
            device_type=args.device_type
        )
        tests.append(("Command Execution", command_passed))
    
    if not args.skip_backup:
        # Test device backup
        backup_passed = test_gateway_backup(
            host=args.host,
            username=args.username,
            password=args.password,
            device_type=args.device_type
        )
        tests.append(("Device Backup", backup_passed))
    
    if not args.skip_scheduled:
        # Test scheduled backup
        scheduled_backup_passed = test_scheduled_backup(
            host=args.host,
            username=args.username,
            password=args.password,
            device_type=args.device_type
        )
        tests.append(("Scheduled Backup", scheduled_backup_passed))
        
        # Test scheduled command
        scheduled_command_passed = test_scheduled_command(
            host=args.host,
            username=args.username,
            password=args.password,
            command=args.command,
            device_type=args.device_type
        )
        tests.append(("Scheduled Command", scheduled_command_passed))
    
    # Check job logs
    logs_passed = check_job_logs()
    tests.append(("Job Logs", logs_passed))
    
    # Print summary
    print("\n=== Test Summary ===")
    all_passed = True
    for name, passed in tests:
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    # Return success if all tests passed
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 