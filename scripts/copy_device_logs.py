#!/usr/bin/env python3
"""
Script to copy device communication logs from the main log file to the jobs log file.

This script reads the main log file, extracts device communication logs,
and appends them to the jobs log file.
"""

import re
import os
from pathlib import Path

def copy_device_logs():
    """Copy device communication logs to the jobs log file."""
    # Define log file paths
    main_log_path = Path("logs/netraven.log")
    jobs_log_path = Path("logs/jobs.log")
    
    # Check if log files exist
    if not main_log_path.exists():
        print(f"Main log file not found: {main_log_path}")
        return
    
    # Create jobs log directory if it doesn't exist
    jobs_log_path.parent.mkdir(exist_ok=True)
    
    # Read the main log file
    with open(main_log_path, "r") as main_log:
        main_log_content = main_log.readlines()
    
    # Filter for device communication logs
    device_comm_logs = []
    for line in main_log_content:
        if "netraven.jobs.device_comm" in line:
            device_comm_logs.append(line)
    
    # Append to jobs log file
    with open(jobs_log_path, "a") as jobs_log:
        if device_comm_logs:
            jobs_log.write("\n# Device Communication Logs\n")
            jobs_log.writelines(device_comm_logs)
            print(f"Added {len(device_comm_logs)} device communication log entries to {jobs_log_path}")
        else:
            print("No device communication logs found in the main log file")

if __name__ == "__main__":
    copy_device_logs() 