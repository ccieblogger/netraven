#!/usr/bin/env python3
"""
Demonstration script for the Scheduler Service.

This script demonstrates how to use the scheduler service programmatically.
"""

import time
import uuid
from datetime import datetime, timedelta

from netraven.core.services.scheduler.models import Job, JobStatus, JobPriority, ScheduleType
from netraven.core.services.scheduler.service import get_scheduler_service
from netraven.core.services.scheduler.handlers import get_registry


def print_job_status(job_id):
    """Print the status of a job."""
    scheduler = get_scheduler_service()
    job = scheduler.get_job(job_id)
    
    print(f"Job: {job.name} (ID: {job.id})")
    print(f"  Status: {job.status.name}")
    print(f"  Type: {job.job_type}")
    print(f"  Priority: {job.priority.name}")
    print(f"  Created At: {job.created_at.isoformat() if job.created_at else 'N/A'}")
    print(f"  Scheduled At: {job.scheduled_at.isoformat() if job.scheduled_at else 'N/A'}")
    
    if job.execution_time is not None:
        print(f"  Execution Time: {job.execution_time:.2f}s")
    
    print(f"  Parameters: {', '.join(k for k in job.parameters.keys() if k != 'password')}")
    print()


def main():
    """Main entry point for the demo script."""
    print("Scheduler Service Demo")
    print("=====================")
    
    # Get the scheduler service
    scheduler = get_scheduler_service()
    
    # Check if service is active
    if not scheduler.is_active():
        print("Starting scheduler service...")
        scheduler.start()
    
    # Print service status
    print(f"Service Status: {'Active' if scheduler.is_active() else 'Inactive'}")
    print(f"Worker Threads: {scheduler.get_worker_count()}")
    print(f"Queue Size: {scheduler.get_queue_size()}")
    print(f"Supported Job Types: {', '.join(get_registry().list_job_types())}")
    print()
    
    # Schedule an immediate backup job
    print("Scheduling immediate backup job...")
    backup_job_id = scheduler.schedule_job(
        job_type="backup",
        parameters={
            "device_id": "demo_device",
            "host": "192.168.1.1",
            "username": "admin",
            "password": "password",
            "save_config": True
        },
        name="Demo Backup Job",
        priority=JobPriority.NORMAL,
        schedule_type=ScheduleType.IMMEDIATE
    )
    print(f"Backup job scheduled with ID: {backup_job_id}")
    
    # Schedule a delayed command execution job
    one_minute_later = datetime.now() + timedelta(minutes=1)
    print(f"Scheduling command execution job for {one_minute_later.isoformat()}...")
    command_job_id = scheduler.schedule_job(
        job_type="command_execution",
        parameters={
            "device_id": "demo_device",
            "host": "192.168.1.1",
            "username": "admin",
            "password": "password",
            "command": "show version"
        },
        name="Demo Command Job",
        priority=JobPriority.HIGH,
        schedule_type=ScheduleType.ONE_TIME,
        schedule_time=one_minute_later
    )
    print(f"Command job scheduled with ID: {command_job_id}")
    print()
    
    # Wait for backup job to complete
    print("Waiting for backup job to complete...")
    max_wait = 10  # seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        backup_job = scheduler.get_job(backup_job_id)
        
        if backup_job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            break
        
        time.sleep(0.5)
    
    # Print job statuses
    print("Job statuses:")
    print_job_status(backup_job_id)
    print_job_status(command_job_id)
    
    # Cancel the command job
    print(f"Cancelling command job {command_job_id}...")
    scheduler.cancel_job(command_job_id)
    
    # Print updated status
    print("Updated command job status:")
    print_job_status(command_job_id)
    
    # List all jobs
    print("All jobs:")
    for job in scheduler.get_all_jobs():
        print(f"  {job.id}: {job.name} ({job.status.name})")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()