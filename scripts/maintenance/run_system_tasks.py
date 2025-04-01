#!/usr/bin/env python3
"""
Run NetRaven system tasks like key rotation and maintenance operations.

This script can be used to run system tasks either on-demand or scheduled.
"""

import os
import sys
import time
import signal
import logging
import argparse
import schedule
from datetime import datetime, timedelta

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.core.config import load_config, get_default_config_path
from netraven.core.logging import get_logger
from netraven.scheduler import get_available_tasks, create_task_instance

# Configure argument parser
parser = argparse.ArgumentParser(description='Run NetRaven system tasks')
parser.add_argument('--config', help='Path to configuration file')
parser.add_argument('--task', help='Specific task to run')
parser.add_argument('--list', action='store_true', help='List available tasks')
parser.add_argument('--schedule', help='Schedule to run tasks (daily, weekly, or hourly)')
parser.add_argument('--time', help='Time to run scheduled tasks (HH:MM format)')
parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Logging level')
args = parser.parse_args()

# Configure logging
logging.basicConfig(
    level=getattr(logging, args.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = get_logger("netraven.system_tasks")

# Load configuration
config_path = args.config or os.environ.get("NETRAVEN_CONFIG", get_default_config_path())
config, _ = load_config(config_path)

def run_task(task_name):
    """Run a specific task."""
    logger.info(f"Running task: {task_name}")
    task = create_task_instance(task_name, config.get("tasks", {}).get(task_name, {}))
    
    if not task:
        logger.error(f"Task not found: {task_name}")
        return False
    
    try:
        # Initialize the task
        if not task.initialize():
            logger.error(f"Failed to initialize task: {task_name}")
            return False
        
        # Run the task
        success = task.run()
        
        # Cleanup
        task.cleanup()
        
        if success:
            logger.info(f"Task completed successfully: {task_name}")
        else:
            logger.error(f"Task failed: {task_name}")
        
        return success
    except Exception as e:
        logger.exception(f"Error running task {task_name}: {str(e)}")
        return False

def list_tasks():
    """List all available tasks."""
    tasks = get_available_tasks()
    
    if not tasks:
        print("No tasks available.")
        return
    
    print("\nAvailable Tasks:")
    print("-" * 50)
    for task in tasks:
        print(f"{task['name']}: {task['description']}")
    print("-" * 50)

def run_all_tasks():
    """Run all available tasks."""
    tasks = get_available_tasks()
    
    if not tasks:
        logger.warning("No tasks available.")
        return
    
    for task in tasks:
        run_task(task["name"])

def main():
    """Main entry point for the system tasks runner."""
    if args.list:
        list_tasks()
        return 0
    
    if args.task:
        # Run a specific task
        success = run_task(args.task)
        return 0 if success else 1
    
    if args.schedule:
        # Setup scheduler
        schedule_type = args.schedule.lower()
        
        if schedule_type == "hourly":
            schedule.every().hour.do(run_all_tasks)
            logger.info("Scheduled tasks to run hourly")
        elif schedule_type == "daily":
            if args.time:
                try:
                    hour, minute = map(int, args.time.split(':'))
                    schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_all_tasks)
                    logger.info(f"Scheduled tasks to run daily at {args.time}")
                except:
                    logger.error(f"Invalid time format: {args.time}")
                    return 1
            else:
                schedule.every().day.at("01:00").do(run_all_tasks)
                logger.info("Scheduled tasks to run daily at 01:00")
        elif schedule_type == "weekly":
            if args.time:
                try:
                    hour, minute = map(int, args.time.split(':'))
                    schedule.every().monday.at(f"{hour:02d}:{minute:02d}").do(run_all_tasks)
                    logger.info(f"Scheduled tasks to run weekly on Monday at {args.time}")
                except:
                    logger.error(f"Invalid time format: {args.time}")
                    return 1
            else:
                schedule.every().monday.at("01:00").do(run_all_tasks)
                logger.info("Scheduled tasks to run weekly on Monday at 01:00")
        else:
            logger.error(f"Invalid schedule type: {schedule_type}")
            return 1
        
        # Run scheduler
        logger.info("Starting system tasks scheduler")
        
        try:
            # Handle termination signals
            running = True
            
            def signal_handler(sig, frame):
                """Handle termination signals."""
                nonlocal running
                logger.info(f"Received signal {sig}, shutting down...")
                running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            while running:
                schedule.run_pending()
                time.sleep(1)
                
            return 0
            
        except Exception as e:
            logger.exception(f"Error in scheduler: {str(e)}")
            return 1
    
    # Default: run all tasks once
    run_all_tasks()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 