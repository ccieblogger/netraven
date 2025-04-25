"""Log schemas for the NetRaven API.

This module defines Pydantic models for log-related API operations, including
job logs and connection logs. These schemas are used for returning log 
information to API clients and supporting log filtering and pagination.
"""

from pydantic import Field
from datetime import datetime
from typing import Optional, Union, Literal, Dict, Any, List

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response

# Unified Log Entry Schema
class LogEntry(BaseSchemaWithId):
    timestamp: datetime
    log_type: str
    level: str
    job_id: Optional[int] = None
    device_id: Optional[int] = None
    source: Optional[str] = None
    message: str
    meta: Optional[Dict[str, Any]] = None

# Paginated response for logs
PaginatedLogResponse = create_paginated_response(LogEntry)

# Log Type Metadata
class LogTypeMeta(BaseSchema):
    log_type: str
    description: Optional[str] = None

# Log Level Metadata
class LogLevelMeta(BaseSchema):
    level: str
    description: Optional[str] = None

# Log Stats
class LogStats(BaseSchema):
    total: int
    by_type: Dict[str, int]
    by_level: Dict[str, int]
    last_log_time: Optional[datetime] = None
