#!/usr/bin/env python3
"""
Test script for the backup scheduler.

This script demonstrates how to use the backup scheduler to schedule
and manage backup jobs with database logging.
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.jobs.scheduler import get_scheduler
from netraven.core.config import load_config, get_default_config_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Test the backup scheduler")
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=str(get_default_config_path())
    )
    parser.add_argument(
        "--device", "-d",
        help="Device hostname or IP address",
        required=True
    )
    parser.add_argument(
        "--interval", "-i",
        help="Interval in minutes for testing",
        type=int,
        default=1
    )
    parser.add_argument(
        "--duration", "-t",
        help="Test duration in minutes",
        type=int,
        default=5
    )
    return parser.parse_args()

def main():
    """Main entry point for the test script."""
    args = parse_args()
    
    # Get credentials from environment
    username = os.environ.get("NETRAVEN_USERNAME")
    password = os.environ.get("NETRAVEN_PASSWORD")
    
    if not username or not password:
        logger.error("No credentials provided. Set NETRAVEN_USERNAME and NETRAVEN_PASSWORD environment variables")
        return 1
    
    # Load configuration
    try:
        config, _ = load_config(args.config)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1
    
    # Get scheduler instance
    scheduler = get_scheduler(args.config)
    
    # Schedule a test backup job
    device_id = f"test-{args.device}"
    job_name = f"Test backup for {args.device}"
    
    logger.info(f"Scheduling test backup job for {args.device} every {args.interval} minutes")
    job_id = scheduler.schedule_backup(
        device_id=device_id,
        host=args.device,
        username=username,
        password=password,
        schedule_type="interval",
        schedule_interval=args.interval,
        job_name=job_name
    )
    
    logger.info(f"Scheduled job {job_id}: {job_name}")
    
    # Start the scheduler
    scheduler.start()
    
    # Run for the specified duration
    logger.info(f"Running scheduler for {args.duration} minutes")
    try:
        end_time = time.time() + (args.duration * 60)
        while time.time() < end_time:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    # Cancel the job and stop the scheduler
    logger.info(f"Cancelling job {job_id}")
    scheduler.cancel_job(job_id)
    
    logger.info("Stopping scheduler")
    scheduler.stop()
    
    logger.info("Test completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 