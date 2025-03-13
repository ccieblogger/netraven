#!/usr/bin/env python3
"""
Test script for device communication logging.

This script demonstrates the enhanced job-specific logging 
for device communications in NetRaven.
"""

import os
import uuid
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the job-specific device connector
from netraven.jobs.device_logging import (
    start_job_session,
    end_job_session,
    register_device,
    log_device_connect,
    log_device_connect_success,
    log_device_connect_failure,
    log_device_command,
    log_device_response,
    log_device_disconnect,
    log_backup_success,
    log_backup_failure
)

def simulate_device_backup():
    """Simulate a device backup job with comprehensive logging."""
    # Start a job session
    session_id = start_job_session("Demo backup job")
    print(f"Started job session: {session_id}")
    
    # Create a few test devices
    devices = [
        {
            "id": str(uuid.uuid4()),
            "hostname": "router1.example.com",
            "device_type": "cisco_ios",
        },
        {
            "id": str(uuid.uuid4()),
            "hostname": "switch1.example.com",
            "device_type": "cisco_ios",
        },
        {
            "id": str(uuid.uuid4()),
            "hostname": "firewall1.example.com",
            "device_type": "cisco_asa",
        }
    ]
    
    # Register the devices with the job session
    for device in devices:
        register_device(
            device_id=device["id"],
            hostname=device["hostname"],
            device_type=device["device_type"],
            session_id=session_id
        )
        print(f"Registered device: {device['hostname']}")
    
    print("\nSimulating device backup process...")
    
    # Simulate backup process for each device with delays to make it realistic
    for i, device in enumerate(devices):
        print(f"\nProcessing device {i+1}/{len(devices)}: {device['hostname']}")
        
        # Connection attempt
        print(f"Connecting to {device['hostname']}...")
        log_device_connect(device["id"], session_id)
        time.sleep(1)  # Simulate connection time
        
        # Successful connection for the first two devices, failure for the third
        if i < 2:
            log_device_connect_success(device["id"], session_id)
            print(f"Successfully connected to {device['hostname']}")
            
            # Execute commands
            commands = [
                "show version",
                "show running-config",
                "show interfaces"
            ]
            
            for command in commands:
                print(f"Sending command: {command}")
                log_device_command(device["id"], command, session_id)
                time.sleep(0.5)  # Simulate command execution
                
                # Simulate command response
                response_size = 1000 + i * 500  # Vary the response size
                log_device_response(
                    device["id"], 
                    command, 
                    True, 
                    response_size, 
                    session_id
                )
                print(f"Received response ({response_size} bytes)")
            
            # Disconnect
            log_device_disconnect(device["id"], session_id)
            print(f"Disconnected from {device['hostname']}")
            
            # Log successful backup
            backup_path = f"/tmp/backups/{device['hostname']}.cfg"
            backup_size = 2500 + i * 1000
            log_backup_success(
                device["id"], 
                backup_path, 
                backup_size, 
                session_id
            )
            print(f"Backup saved to {backup_path} ({backup_size} bytes)")
            
        else:
            # Simulate a failure for the third device
            error_msg = "Connection timed out after 30 seconds"
            log_device_connect_failure(device["id"], error_msg, session_id)
            print(f"Failed to connect to {device['hostname']}: {error_msg}")
            
            # Log backup failure
            log_backup_failure(
                device["id"], 
                f"Could not backup device: {error_msg}", 
                session_id
            )
            print(f"Backup failed for {device['hostname']}")
    
    # End the job session
    success = True  # 2 out of 3 devices backed up
    end_job_session(session_id, success)
    print(f"\nJob session {session_id} completed with success={success}")
    print("\nCheck the logs/jobs.log file for detailed job logs.")

if __name__ == "__main__":
    simulate_device_backup() 