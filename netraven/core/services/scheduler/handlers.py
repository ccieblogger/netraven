"""
Task handler interface for the scheduler service.

This module provides the abstract base class for task handlers and a
registry for managing them.
"""

import abc
import logging
from typing import Any, Callable, Dict, List, Type

from netraven.core.services.scheduler.models import Job, JobStatus
from netraven.core.services.scheduler.logging import get_job_logging_service

# Configure logging
logger = logging.getLogger(__name__)


class TaskHandler(abc.ABC):
    """
    Abstract base class for task handlers.
    
    Task handlers are responsible for executing specific job types.
    Each handler provides the logic needed to execute a particular
    type of job, such as backup or command execution.
    """
    
    def __init__(self):
        """Initialize the task handler."""
        self._job_logging_service = get_job_logging_service()
    
    @abc.abstractmethod
    def execute(self, job: Job) -> Dict[str, Any]:
        """
        Execute the job.
        
        Args:
            job: The job to execute
            
        Returns:
            Dictionary with job result information
        """
        pass
    
    def __call__(self, job: Job) -> Dict[str, Any]:
        """
        Make the task handler callable.
        
        This method handles the common logic for job execution, including
        logging job start/completion and updating job status.
        
        Args:
            job: The job to execute
            
        Returns:
            Dictionary with job result information
        """
        try:
            # Update job status to RUNNING
            job.status = JobStatus.RUNNING
            self._log_job_status(job, JobStatus.RUNNING, "Job execution started")
            
            # Execute the job
            result = self.execute(job)
            
            # Update job status based on result
            success = result.get("success", False)
            if success:
                job.status = JobStatus.COMPLETED
                self._job_logging_service.log_job_completion(job, result)
            else:
                job.status = JobStatus.FAILED
                message = result.get("message", "Job failed")
                self._log_job_status(job, JobStatus.FAILED, message)
            
            return result
        except Exception as e:
            # Handle exceptions during execution
            job.status = JobStatus.FAILED
            self._job_logging_service.log_job_failure(job, e)
            logger.exception(f"Error executing job {job.id}: {str(e)}")
            
            # Re-raise the exception to notify the caller
            raise
    
    def _log_job_status(self, job: Job, status: JobStatus, message: str = None) -> None:
        """
        Log a job status change.
        
        Args:
            job: The job whose status is changing
            status: The new status
            message: Optional message with additional details
        """
        self._job_logging_service.log_job_status(job, status, message)


class TaskHandlerRegistry:
    """
    Registry for task handlers.
    
    This class manages the registration and retrieval of task handlers
    for different job types.
    """
    
    def __init__(self):
        """Initialize the task handler registry."""
        self._handlers = {}
    
    def register_handler(self, job_type: str, handler: TaskHandler) -> None:
        """
        Register a handler for a specific job type.
        
        Args:
            job_type: The type of job the handler can execute
            handler: The task handler instance
            
        Raises:
            ValueError: If a handler is already registered for the job type
        """
        if job_type in self._handlers:
            raise ValueError(f"Handler already registered for job type: {job_type}")
        
        logger.info(f"Registering handler for job type: {job_type}")
        self._handlers[job_type] = handler
    
    def get_handler(self, job_type: str) -> TaskHandler:
        """
        Get the handler for a specific job type.
        
        Args:
            job_type: The type of job to get a handler for
            
        Returns:
            The task handler for the specified job type
            
        Raises:
            ValueError: If no handler is registered for the job type
        """
        if job_type not in self._handlers:
            raise ValueError(f"No handler registered for job type: {job_type}")
        
        return self._handlers[job_type]
    
    def list_job_types(self) -> List[str]:
        """
        List all registered job types.
        
        Returns:
            List of registered job types
        """
        return list(self._handlers.keys())


# Singleton instance of the registry
_registry = None


def get_registry() -> TaskHandlerRegistry:
    """
    Get the singleton instance of the task handler registry.
    
    Returns:
        The task handler registry instance
    """
    global _registry
    if _registry is None:
        _registry = TaskHandlerRegistry()
    
    return _registry


def register_handler(job_type: str, handler: TaskHandler) -> None:
    """
    Register a handler for a specific job type.
    
    This is a convenience function that gets the registry instance
    and registers the handler.
    
    Args:
        job_type: The type of job the handler can execute
        handler: The task handler instance
    """
    registry = get_registry()
    registry.register_handler(job_type, handler)


def task_handler(job_type: str) -> Callable[[Type[TaskHandler]], Type[TaskHandler]]:
    """
    Decorator for registering a task handler class.
    
    This decorator creates an instance of the decorated class
    and registers it with the registry.
    
    Args:
        job_type: The type of job the handler can execute
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[TaskHandler]) -> Type[TaskHandler]:
        if not issubclass(cls, TaskHandler):
            raise TypeError(f"Class {cls.__name__} is not a subclass of TaskHandler")
        
        # Create an instance of the handler and register it
        handler = cls()
        register_handler(job_type, handler)
        
        return cls
    
    return decorator


def register_function_handler(job_type: str, func: Callable[[Job], Dict[str, Any]]) -> None:
    """
    Register a function as a task handler.
    
    This function creates a simple task handler that wraps the
    provided function and registers it with the registry.
    
    Args:
        job_type: The type of job the handler can execute
        func: The function to use as the handler
    """
    class FunctionTaskHandler(TaskHandler):
        def execute(self, job: Job) -> Dict[str, Any]:
            return func(job)
    
    handler = FunctionTaskHandler()
    register_handler(job_type, handler) 