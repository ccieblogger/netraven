"""
Scheduler package for NetRaven system tasks.

This package provides functionality for scheduling and executing system tasks
like key rotation and maintenance operations.
"""

import importlib
import logging
import os
import pkgutil
from typing import Dict, List, Optional, Type

from netraven.core.logging import get_logger
from netraven.scheduler.task import ScheduledTask

# Configure logging
logger = get_logger("netraven.scheduler")

# Registry of available tasks
_task_registry: Dict[str, Type[ScheduledTask]] = {}

def discover_tasks():
    """
    Discover all available tasks in the system.
    
    This function scans the tasks directory and registers all task classes 
    that inherit from ScheduledTask.
    """
    from netraven.scheduler import tasks
    
    # Get the tasks package directory
    package_dir = os.path.dirname(tasks.__file__)
    
    # Load all modules in the tasks package
    for _, name, is_pkg in pkgutil.iter_modules([package_dir]):
        if is_pkg:
            continue
            
        try:
            # Import the module
            module = importlib.import_module(f"netraven.scheduler.tasks.{name}")
            
            # Find all classes in the module that are subclasses of ScheduledTask
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, ScheduledTask) and 
                    attr is not ScheduledTask):
                    # Register the task
                    task_name = getattr(attr, "NAME", attr_name.lower())
                    _task_registry[task_name] = attr
                    logger.debug(f"Registered task: {task_name}")
        except Exception as e:
            logger.error(f"Error loading task module {name}: {str(e)}")
    
    logger.info(f"Discovered {len(_task_registry)} tasks")

def get_available_tasks() -> List[Dict]:
    """
    Get a list of all available tasks.
    
    Returns:
        List of dictionaries with task information
    """
    if not _task_registry:
        discover_tasks()
        
    return [
        {
            "name": task_name,
            "description": task_class.DESCRIPTION
        }
        for task_name, task_class in _task_registry.items()
    ]

def get_task_class(task_name: str) -> Optional[Type[ScheduledTask]]:
    """
    Get the task class for a given task name.
    
    Args:
        task_name: Name of the task
        
    Returns:
        Task class or None if not found
    """
    if not _task_registry:
        discover_tasks()
        
    return _task_registry.get(task_name)

def create_task_instance(task_name: str, config=None) -> Optional[ScheduledTask]:
    """
    Create an instance of a task.
    
    Args:
        task_name: Name of the task
        config: Task configuration
        
    Returns:
        Task instance or None if task not found
    """
    task_class = get_task_class(task_name)
    if not task_class:
        return None
        
    return task_class(config) 