"""Log schemas for the NetRaven API.

This module defines Pydantic models for log-related API operations, including
job logs and connection logs. These schemas are used for returning log 
information to API clients and supporting log filtering and pagination.
"""

from pydantic import Field
from datetime import datetime
from typing import Optional, Union, Literal

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from netraven.db.models.job_log import LogLevel # Import enum

# --- Log Schemas (JobLog & ConnectionLog) ---

class JobLog(BaseSchemaWithId):
    """Schema for job log entries.
    
    Represents log entries generated during job execution, providing
    information about job progress, errors, and events.
    
    Attributes:
        id: Primary key identifier for the log entry
        job_id: Foreign key reference to the associated Job
        device_id: Optional foreign key reference to a specific Device
        message: The log message text
        level: Severity level of the log entry (from LogLevel enum)
        timestamp: When the log entry was created
        log_type: Discriminator field to identify this as a job log
    """
    job_id: int
    device_id: Optional[int] = None # Nullable as per model
    message: str
    level: LogLevel # Use the enum
    timestamp: datetime
    log_type: Literal["job_log"] = "job_log"

class ConnectionLog(BaseSchemaWithId):
    """Schema for connection log entries.
    
    Represents raw output and metadata from device connection attempts,
    providing troubleshooting information for connections to network devices.
    
    Attributes:
        id: Primary key identifier for the log entry
        job_id: Foreign key reference to the Job that initiated the connection
        device_id: Foreign key reference to the Device being connected to
        log: Raw text output from the device connection interaction
        timestamp: When the connection attempt occurred
        log_type: Discriminator field to identify this as a connection log
    """
    job_id: int
    device_id: int
    log: str # The actual (redacted) log content
    timestamp: datetime
    log_type: Literal["connection_log"] = "connection_log"

# Combined Log Type (for mixed results)
CombinedLog = Union[JobLog, ConnectionLog]
"""Union type for representing either job logs or connection logs.

This type is used when API endpoints may return a mixture of both log types,
using the log_type field as a discriminator to determine the actual schema.
"""

# Paginated response models
PaginatedJobLogResponse = create_paginated_response(JobLog)
PaginatedConnectionLogResponse = create_paginated_response(ConnectionLog)
PaginatedCombinedLogResponse = create_paginated_response(CombinedLog)
