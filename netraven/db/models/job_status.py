"""Job status enum for NetRaven.

This module defines the possible status values for jobs in the NetRaven system.
The enum provides a consistent set of status values that can be used throughout
the application.

Status values indicate the current state of a job, including normal execution
statuses as well as various failure conditions. Credential-related statuses
are included to handle credential resolution scenarios.
"""

from enum import Enum


class JobStatus(str, Enum):
    """Status values for jobs."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_PARTIAL_FAILURE = "COMPLETED_PARTIAL_FAILURE"
    COMPLETED_FAILURE = "COMPLETED_FAILURE"
    COMPLETED_NO_DEVICES = "COMPLETED_NO_DEVICES"
    FAILED_UNEXPECTED = "FAILED_UNEXPECTED"
    FAILED_DISPATCHER_ERROR = "FAILED_DISPATCHER_ERROR"
    
    # Credential-related statuses
    COMPLETED_NO_CREDENTIALS = "COMPLETED_NO_CREDENTIALS"
    FAILED_CREDENTIAL_RESOLUTION = "FAILED_CREDENTIAL_RESOLUTION" 