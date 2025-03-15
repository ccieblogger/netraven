#!/usr/bin/env python3
"""
Run the NetRaven scheduler as a standalone service.

This script starts the scheduler service to process scheduled jobs
without requiring the full web application to be running.
"""

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger
from netraven.jobs.scheduler import get_scheduler, BackupScheduler
from netraven.web.database import get_db, init_db
from netraven.web.crud.scheduled_job import get_scheduled_jobs, get_scheduled_job, get_due_jobs, update_job_last_run
from netraven.web.crud.device import get_device
from netraven.web.schemas.scheduled_job import ScheduledJobFilter

# Configure argument parser
parser = argparse.ArgumentParser(description='Run the NetRaven scheduler as a standalone service')
parser.add_argument('--config', help='Path to configuration file')
parser.add_argument('--check-interval', type=int, default=60, help='Interval in seconds to check for due jobs')
parser.add_argument('--sync-interval', type=int, default=300, help='Interval in seconds to sync with database')
parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Logging level')
args = parser.parse_args()

# Load configuration
config_path = args.config or os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

# Setup logging
logging.basicConfig(
    level=getattr(logging, args.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = get_logger("netraven.scheduler")

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")
    sys.exit(1)

# Initialize scheduler
scheduler = get_scheduler()
db_session = next(get_db())
job_map = {}  # Maps database job IDs to scheduler job IDs

# Track last sync time
last_sync_time = datetime.now()

# Handle termination signals
running = True

def signal_handler(sig, frame):
    """Handle termination signals."""
    global running
    logger.info(f"Received signal {sig}, shutting down...")
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def load_jobs_from_db():
    """Load all enabled scheduled jobs from the database."""
    try:
        # Create filter for enabled jobs
        filter_params = ScheduledJobFilter(enabled=True)
        
        # Get all enabled jobs
        jobs = get_scheduled_jobs(db_session, filter_params=filter_params)
        count = 0
        
        for job in jobs:
            # Get device details
            device = get_device(db_session, job.device_id)
            if not device:
                logger.warning(f"Device {job.device_id} not found for job {job.id}")
                continue
            
            # Schedule the job
            scheduler_job_id = scheduler.schedule_backup(
                device_id=device.id,
                host=device.hostname,
                username=device.username,
                password=device.password,
                device_type=device.device_type,
                schedule_type=job.schedule_type,
                schedule_time=job.schedule_time,
                schedule_interval=job.schedule_interval,
                schedule_day=job.schedule_day,
                job_name=job.name
            )
            
            # Map database job ID to scheduler job ID
            job_map[job.id] = scheduler_job_id
            count += 1
        
        logger.info(f"Loaded {count} scheduled jobs from database")
        return count
    except Exception as e:
        logger.exception(f"Error loading jobs from database: {e}")
        return 0

def sync_with_db():
    """Sync scheduler with database."""
    try:
        # Get all jobs from database
        jobs = get_scheduled_jobs(db_session)
        
        # Track changes
        added = 0
        removed = 0
        
        # Check for new or re-enabled jobs
        for job in jobs:
            if job.enabled and job.id not in job_map:
                # New or re-enabled job
                device = get_device(db_session, job.device_id)
                if not device:
                    logger.warning(f"Device {job.device_id} not found for job {job.id}")
                    continue
                
                # Schedule the job
                scheduler_job_id = scheduler.schedule_backup(
                    device_id=device.id,
                    host=device.hostname,
                    username=device.username,
                    password=device.password,
                    device_type=device.device_type,
                    schedule_type=job.schedule_type,
                    schedule_time=job.schedule_time,
                    schedule_interval=job.schedule_interval,
                    schedule_day=job.schedule_day,
                    job_name=job.name
                )
                
                # Map database job ID to scheduler job ID
                job_map[job.id] = scheduler_job_id
                added += 1
            elif not job.enabled and job.id in job_map:
                # Disabled job
                scheduler_job_id = job_map[job.id]
                scheduler.cancel_job(scheduler_job_id)
                del job_map[job.id]
                removed += 1
        
        # Check for deleted jobs
        db_job_ids = {job.id for job in jobs}
        for db_job_id in list(job_map.keys()):
            if db_job_id not in db_job_ids:
                # Job deleted from database
                scheduler_job_id = job_map[db_job_id]
                scheduler.cancel_job(scheduler_job_id)
                del job_map[db_job_id]
                removed += 1
        
        logger.info(f"Synced scheduler with database: added {added}, removed {removed}")
        return {"added": added, "removed": removed}
    except Exception as e:
        logger.exception(f"Error syncing with database: {e}")
        return {"added": 0, "removed": 0}

def run_job(job_id, user_id=None):
    """Run a scheduled job immediately."""
    try:
        # Get job from database
        job = get_scheduled_job(db_session, job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return False
        
        # Get device details
        device = get_device(db_session, job.device_id)
        if not device:
            logger.warning(f"Device {job.device_id} not found for job {job_id}")
            return False
        
        # Run the job
        from netraven.jobs.device_connector import backup_device_config
        
        logger.info(f"Running job {job_id} for device {device.hostname}")
        result = backup_device_config(
            device_id=device.id,
            host=device.hostname,
            username=device.username,
            password=device.password,
            device_type=device.device_type,
            user_id=user_id or job.created_by
        )
        
        # Update last run time
        update_job_last_run(db_session, job_id)
        
        return result
    except Exception as e:
        logger.exception(f"Error running job {job_id}: {e}")
        return False

def check_due_jobs():
    """Check for due jobs and run them."""
    try:
        # Get due jobs
        due_jobs = get_due_jobs(db_session)
        count = 0
        
        for job in due_jobs:
            # Run the job
            result = run_job(job.id)
            if result:
                count += 1
        
        if count > 0:
            logger.info(f"Ran {count} due jobs")
        return count
    except Exception as e:
        logger.exception(f"Error checking due jobs: {e}")
        return 0

# Start scheduler
logger.info("Starting scheduler")
load_jobs_from_db()
scheduler.start()

try:
    # Main loop
    while running:
        try:
            # Check for due jobs
            count = check_due_jobs()
            
            # Sync with database periodically
            now = datetime.now()
            if now - last_sync_time > timedelta(seconds=args.sync_interval):
                result = sync_with_db()
                last_sync_time = now
            
            # Sleep for check interval
            time.sleep(args.check_interval)
        except Exception as e:
            logger.exception(f"Error in scheduler loop: {e}")
            # Continue running despite errors
            time.sleep(args.check_interval)
finally:
    # Stop scheduler
    logger.info("Stopping scheduler")
    scheduler.stop()
    logger.info("Scheduler stopped") 