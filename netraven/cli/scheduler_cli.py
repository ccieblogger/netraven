#!/usr/bin/env python3
"""
Command-line interface for the Scheduler Service.

This module provides a command-line interface for interacting with the
scheduler service, allowing users to schedule jobs, view job status,
and manage the service.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from netraven.core.services.scheduler.models import Job, JobStatus, JobPriority, ScheduleType
from netraven.core.services.scheduler.service import get_scheduler_service
from netraven.core.services.scheduler.handlers import get_registry


def format_job(job: Job) -> Dict[str, Any]:
    """
    Format a job for display.
    
    Args:
        job: Job to format
        
    Returns:
        Dictionary with formatted job information
    """
    result = {
        "id": job.id,
        "name": job.name,
        "type": job.job_type,
        "status": job.status.name,
        "priority": job.priority.name,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
        "parameters": {k: v for k, v in job.parameters.items() if k != "password"}
    }
    
    if job.execution_time is not None:
        result["execution_time"] = f"{job.execution_time:.2f}s"
    
    return result


def list_jobs(args: argparse.Namespace) -> None:
    """
    List all jobs in the scheduler.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    # Get jobs based on status filter
    if args.status:
        try:
            status = JobStatus[args.status.upper()]
            jobs = [job for job in scheduler.get_all_jobs() if job.status == status]
        except KeyError:
            print(f"Error: Invalid status '{args.status}'. Valid values: {', '.join(s.name.lower() for s in JobStatus)}")
            sys.exit(1)
    else:
        jobs = scheduler.get_all_jobs()
    
    # Format jobs for display
    formatted_jobs = [format_job(job) for job in jobs]
    
    # Display jobs
    if args.json:
        print(json.dumps(formatted_jobs, indent=2))
    else:
        if not jobs:
            print("No jobs found.")
            return
        
        # Print table header
        print(f"{'ID':<36} {'Name':<30} {'Type':<20} {'Status':<10} {'Priority':<10} {'Scheduled At':<25}")
        print("-" * 130)
        
        # Print jobs
        for job in jobs:
            scheduled_at = job.scheduled_at.isoformat() if job.scheduled_at else "N/A"
            print(f"{job.id:<36} {job.name:<30} {job.job_type:<20} {job.status.name:<10} {job.priority.name:<10} {scheduled_at:<25}")


def show_job(args: argparse.Namespace) -> None:
    """
    Show details of a specific job.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    try:
        job = scheduler.get_job(args.job_id)
    except ValueError:
        print(f"Error: Job with ID '{args.job_id}' not found.")
        sys.exit(1)
    
    # Format job for display
    formatted_job = format_job(job)
    
    # Display job
    if args.json:
        print(json.dumps(formatted_job, indent=2))
    else:
        print(f"Job ID: {job.id}")
        print(f"Name: {job.name}")
        print(f"Type: {job.job_type}")
        print(f"Status: {job.status.name}")
        print(f"Priority: {job.priority.name}")
        print(f"Created At: {job.created_at.isoformat() if job.created_at else 'N/A'}")
        print(f"Scheduled At: {job.scheduled_at.isoformat() if job.scheduled_at else 'N/A'}")
        
        if job.execution_time is not None:
            print(f"Execution Time: {job.execution_time:.2f}s")
        
        print("\nParameters:")
        for key, value in job.parameters.items():
            if key != "password":
                print(f"  {key}: {value}")


def schedule_backup(args: argparse.Namespace) -> None:
    """
    Schedule a backup job.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    # Create job parameters
    parameters = {
        "device_id": args.device_id,
        "host": args.host,
        "username": args.username,
        "password": args.password,
        "save_config": not args.no_save
    }
    
    # Determine schedule type
    if args.now:
        schedule_type = ScheduleType.IMMEDIATE
        schedule_time = None
    elif args.cron:
        schedule_type = ScheduleType.CRON
        schedule_time = args.cron
    else:
        schedule_type = ScheduleType.ONE_TIME
        if args.time:
            try:
                schedule_time = datetime.fromisoformat(args.time)
            except ValueError:
                print(f"Error: Invalid time format. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)
        else:
            # Schedule for 1 minute from now
            schedule_time = datetime.now().replace(microsecond=0, second=0) + datetime.timedelta(minutes=1)
    
    # Schedule job
    job_id = scheduler.schedule_job(
        job_type="backup",
        parameters=parameters,
        name=args.name or f"Backup job for {args.host}",
        priority=JobPriority[args.priority.upper()],
        schedule_type=schedule_type,
        schedule_time=schedule_time
    )
    
    print(f"Scheduled backup job with ID: {job_id}")
    
    # Wait for job completion if requested
    if args.wait:
        wait_for_job(job_id)


def schedule_command(args: argparse.Namespace) -> None:
    """
    Schedule a command execution job.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    # Create job parameters
    parameters = {
        "device_id": args.device_id,
        "host": args.host,
        "username": args.username,
        "password": args.password,
        "command": args.command
    }
    
    # Determine schedule type
    if args.now:
        schedule_type = ScheduleType.IMMEDIATE
        schedule_time = None
    elif args.cron:
        schedule_type = ScheduleType.CRON
        schedule_time = args.cron
    else:
        schedule_type = ScheduleType.ONE_TIME
        if args.time:
            try:
                schedule_time = datetime.fromisoformat(args.time)
            except ValueError:
                print(f"Error: Invalid time format. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)
        else:
            # Schedule for 1 minute from now
            schedule_time = datetime.now().replace(microsecond=0, second=0) + datetime.timedelta(minutes=1)
    
    # Schedule job
    job_id = scheduler.schedule_job(
        job_type="command_execution",
        parameters=parameters,
        name=args.name or f"Command job for {args.host}",
        priority=JobPriority[args.priority.upper()],
        schedule_type=schedule_type,
        schedule_time=schedule_time
    )
    
    print(f"Scheduled command execution job with ID: {job_id}")
    
    # Wait for job completion if requested
    if args.wait:
        wait_for_job(job_id)


def cancel_job(args: argparse.Namespace) -> None:
    """
    Cancel a job.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    try:
        scheduler.cancel_job(args.job_id)
        print(f"Cancelled job with ID: {args.job_id}")
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


def service_status(args: argparse.Namespace) -> None:
    """
    Show scheduler service status.
    
    Args:
        args: Command-line arguments
    """
    scheduler = get_scheduler_service()
    
    status = {
        "active": scheduler.is_active(),
        "worker_count": scheduler.get_worker_count(),
        "queue_size": scheduler.get_queue_size(),
        "job_types": get_registry().list_job_types()
    }
    
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print(f"Service Status: {'Active' if status['active'] else 'Inactive'}")
        print(f"Worker Threads: {status['worker_count']}")
        print(f"Queue Size: {status['queue_size']}")
        print(f"Supported Job Types: {', '.join(status['job_types'])}")


def wait_for_job(job_id: str, timeout: int = 60) -> None:
    """
    Wait for a job to complete.
    
    Args:
        job_id: ID of the job to wait for
        timeout: Maximum time to wait in seconds
    """
    scheduler = get_scheduler_service()
    
    print(f"Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            job = scheduler.get_job(job_id)
            
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                print(f"Job {job_id} finished with status: {job.status.name}")
                
                if job.status == JobStatus.COMPLETED:
                    print(f"Execution time: {job.execution_time:.2f}s")
                
                return
            
            print(f"Current status: {job.status.name}")
            time.sleep(1)
            
        except ValueError:
            print(f"Error: Job with ID '{job_id}' not found.")
            sys.exit(1)
    
    print(f"Timeout waiting for job {job_id} to complete.")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Scheduler Service CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # List jobs command
    list_parser = subparsers.add_parser("list", parents=[common_parser], help="List all jobs")
    list_parser.add_argument("--status", help="Filter by job status")
    list_parser.set_defaults(func=list_jobs)
    
    # Show job command
    show_parser = subparsers.add_parser("show", parents=[common_parser], help="Show job details")
    show_parser.add_argument("job_id", help="ID of the job to show")
    show_parser.set_defaults(func=show_job)
    
    # Common arguments for scheduling jobs
    schedule_parser = argparse.ArgumentParser(add_help=False)
    schedule_parser.add_argument("--device-id", required=True, help="Device ID")
    schedule_parser.add_argument("--host", required=True, help="Device hostname or IP address")
    schedule_parser.add_argument("--username", required=True, help="Device username")
    schedule_parser.add_argument("--password", required=True, help="Device password")
    schedule_parser.add_argument("--name", help="Job name")
    schedule_parser.add_argument("--priority", choices=["low", "normal", "high"], default="normal", help="Job priority")
    schedule_parser.add_argument("--now", action="store_true", help="Execute job immediately")
    schedule_parser.add_argument("--time", help="Schedule time (ISO format)")
    schedule_parser.add_argument("--cron", help="Cron expression for recurring jobs")
    schedule_parser.add_argument("--wait", action="store_true", help="Wait for job completion")
    
    # Schedule backup command
    backup_parser = subparsers.add_parser("backup", parents=[schedule_parser], help="Schedule a backup job")
    backup_parser.add_argument("--no-save", action="store_true", help="Don't save the configuration")
    backup_parser.set_defaults(func=schedule_backup)
    
    # Schedule command execution job
    command_parser = subparsers.add_parser("command", parents=[schedule_parser], help="Schedule a command execution job")
    command_parser.add_argument("--command", required=True, help="Command to execute")
    command_parser.set_defaults(func=schedule_command)
    
    # Cancel job command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="ID of the job to cancel")
    cancel_parser.set_defaults(func=cancel_job)
    
    # Service status command
    status_parser = subparsers.add_parser("status", parents=[common_parser], help="Show service status")
    status_parser.set_defaults(func=service_status)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 