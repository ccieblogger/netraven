"""
Scheduler service models for NetRaven.

This module provides the core model classes for the scheduler service,
including Job, JobStatus, and JobPriority definitions.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum, auto


class JobStatus(Enum):
    """Enumeration of possible job statuses."""
    QUEUED = 1      # Job is created but not yet in the queue
    PENDING = 2     # Job is in the queue waiting to be executed
    RUNNING = 3     # Job is currently being executed
    COMPLETED = 4   # Job has completed successfully
    FAILED = 5      # Job has failed
    CANCELED = 6    # Job was canceled
    PAUSED = 7      # Job is paused


class JobPriority(Enum):
    """Enumeration of job priority levels, with higher values indicating higher priority."""
    CRITICAL = 100  # Critical priority - execute immediately
    HIGH = 80       # High priority
    NORMAL = 50     # Normal priority
    LOW = 30        # Low priority
    LOWEST = 10     # Lowest priority - execute when nothing else is pending


class ScheduleType(Enum):
    """Enumeration of job scheduling types."""
    IMMEDIATE = 1   # Run immediately
    ONE_TIME = 2    # Run once at a specific time
    DAILY = 3       # Run daily
    WEEKLY = 4      # Run weekly
    MONTHLY = 5     # Run monthly
    YEARLY = 6      # Run yearly
    CRON = 7        # Run according to a cron expression


class JobDefinition:
    """
    Job definition with scheduling information.
    
    This class encapsulates the definition of a job, including its type,
    parameters, and scheduling information. It can be used to create
    new jobs for scheduling.
    """
    
    def __init__(
        self,
        job_type: str,
        parameters: Dict[str, Any] = None,
        schedule_type: Union[ScheduleType, str] = ScheduleType.IMMEDIATE,
        priority: Union[JobPriority, str] = JobPriority.NORMAL,
        job_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a job definition.
        
        Args:
            job_type: Type of job to execute
            parameters: Parameters for the job
            schedule_type: Type of schedule for the job
            priority: Priority of the job
            job_id: ID of the job (optional, will be generated if not provided)
            name: Name of the job (optional)
            description: Description of the job (optional)
            metadata: Additional metadata for the job (optional)
        """
        self.job_type = job_type
        self.parameters = parameters or {}
        
        # Convert string to enum if needed
        if isinstance(schedule_type, str):
            self.schedule_type = ScheduleType[schedule_type]
        else:
            self.schedule_type = schedule_type
        
        # Convert string to enum if needed
        if isinstance(priority, str):
            self.priority = JobPriority[priority]
        else:
            self.priority = priority
        
        self.id = job_id
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        
        # Validate schedule parameters
        self._validate_schedule_parameters()
    
    def _validate_schedule_parameters(self) -> None:
        """
        Validate that the required parameters for the schedule type are present.
        
        Raises:
            ValueError: If required parameters are missing
        """
        if self.schedule_type == ScheduleType.ONE_TIME:
            if "schedule_time" not in self.parameters:
                raise ValueError("ONE_TIME schedule requires a 'schedule_time' parameter")
        
        elif self.schedule_type == ScheduleType.DAILY:
            # Check for hour and minute
            if "hour" not in self.parameters:
                self.parameters["hour"] = 0
            if "minute" not in self.parameters:
                self.parameters["minute"] = 0
        
        elif self.schedule_type == ScheduleType.WEEKLY:
            # Check for day_of_week, hour, and minute
            if "day_of_week" not in self.parameters:
                self.parameters["day_of_week"] = 0  # Monday
            if "hour" not in self.parameters:
                self.parameters["hour"] = 0
            if "minute" not in self.parameters:
                self.parameters["minute"] = 0
        
        elif self.schedule_type == ScheduleType.MONTHLY:
            # Check for day_of_month, hour, and minute
            if "day_of_month" not in self.parameters:
                self.parameters["day_of_month"] = 1
            if "hour" not in self.parameters:
                self.parameters["hour"] = 0
            if "minute" not in self.parameters:
                self.parameters["minute"] = 0
        
        elif self.schedule_type == ScheduleType.YEARLY:
            # Check for month, day, hour, and minute
            if "month" not in self.parameters:
                self.parameters["month"] = 1
            if "day" not in self.parameters:
                self.parameters["day"] = 1
            if "hour" not in self.parameters:
                self.parameters["hour"] = 0
            if "minute" not in self.parameters:
                self.parameters["minute"] = 0
        
        elif self.schedule_type == ScheduleType.CRON:
            if "cron_expression" not in self.parameters:
                raise ValueError("CRON schedule requires a 'cron_expression' parameter")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert job definition to a dictionary.
        
        Returns:
            Dictionary representation of the job definition
        """
        return {
            "id": self.id,
            "job_type": self.job_type,
            "parameters": self.parameters,
            "schedule_type": self.schedule_type.name,
            "priority": self.priority.name,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobDefinition':
        """
        Create a job definition from a dictionary.
        
        Args:
            data: Dictionary representation of the job definition
            
        Returns:
            JobDefinition instance
        """
        return cls(
            job_type=data["job_type"],
            parameters=data.get("parameters", {}),
            schedule_type=data.get("schedule_type", ScheduleType.IMMEDIATE.name),
            priority=data.get("priority", JobPriority.NORMAL.name),
            job_id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            metadata=data.get("metadata", {})
        )


class Job:
    """
    Representation of a scheduled or running job.
    
    This class extends JobDefinition with runtime information, including
    current status, execution history, and results.
    """
    
    def __init__(
        self,
        definition: JobDefinition,
        status: JobStatus = JobStatus.QUEUED,
        created_at: Optional[datetime] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        next_run: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        retry_count: int = 0,
        execution_history: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize a job.
        
        Args:
            definition: Job definition
            status: Current status of the job
            created_at: Creation timestamp
            started_at: Execution start timestamp
            completed_at: Execution completion timestamp
            next_run: Next scheduled run timestamp
            result: Execution result data
            error: Error message if job failed
            retry_count: Number of retry attempts made
            execution_history: History of previous executions
        """
        self.definition = definition
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.started_at = started_at
        self.completed_at = completed_at
        self.next_run = next_run
        self.result = result or {}
        self.error = error
        self.retry_count = retry_count
        self.execution_history = execution_history or []
    
    @property
    def id(self) -> str:
        """Get the job ID."""
        return self.definition.id
    
    @property
    def job_type(self) -> str:
        """Get the job type."""
        return self.definition.job_type
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """Get the job parameters."""
        return self.definition.parameters
    
    @property
    def priority(self) -> JobPriority:
        """Get the job priority."""
        return self.definition.priority
    
    @property
    def device_id(self) -> Optional[str]:
        """Get the device ID."""
        return self.definition.device_id
    
    def is_terminal(self) -> bool:
        """Check if the job is in a terminal state."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELED]
    
    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return (
            self.status == JobStatus.FAILED and
            self.retry_count < self.definition.max_retries
        )
    
    def add_execution_record(self, success: bool, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        """
        Add an execution record to the history.
        
        Args:
            success: Whether the execution was successful
            result: Execution result data
            error: Error message if execution failed
        """
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
            "result": result,
            "error": error,
            "retry_count": self.retry_count
        }
        self.execution_history.append(record)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the job to a dictionary.
        
        Returns:
            Dict representation of the job
        """
        return {
            "definition": self.definition.to_dict(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "execution_history": self.execution_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """
        Create a job from a dictionary.
        
        Args:
            data: Dictionary containing job data
            
        Returns:
            Job instance
        """
        # Create job definition from definition data
        definition = JobDefinition.from_dict(data.get("definition", {}))
        
        # Convert string status to enum
        status = data.get("status")
        if isinstance(status, int):
            status = JobStatus(status)
        
        # Convert ISO timestamp strings to datetime
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                created_at = datetime.utcnow()
        
        started_at = data.get("started_at")
        if started_at and isinstance(started_at, str):
            try:
                started_at = datetime.fromisoformat(started_at)
            except ValueError:
                started_at = None
        
        completed_at = data.get("completed_at")
        if completed_at and isinstance(completed_at, str):
            try:
                completed_at = datetime.fromisoformat(completed_at)
            except ValueError:
                completed_at = None
        
        next_run = data.get("next_run")
        if next_run and isinstance(next_run, str):
            try:
                next_run = datetime.fromisoformat(next_run)
            except ValueError:
                next_run = None
        
        return cls(
            definition=definition,
            status=status or JobStatus.QUEUED,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            next_run=next_run,
            result=data.get("result", {}),
            error=data.get("error"),
            retry_count=data.get("retry_count", 0),
            execution_history=data.get("execution_history", [])
        ) 