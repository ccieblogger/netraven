from pydantic import Field
from datetime import datetime
from typing import Optional, Union, Literal

from .base import BaseSchema, BaseSchemaWithId, create_paginated_response
from netraven.db.models.job_log import LogLevel # Import enum

# --- Log Schemas (JobLog & ConnectionLog) ---

# JobLog Read Schema
class JobLog(BaseSchemaWithId):
    job_id: int
    device_id: Optional[int] = None # Nullable as per model
    message: str
    level: LogLevel # Use the enum
    timestamp: datetime
    log_type: Literal["job_log"] = "job_log"

# ConnectionLog Read Schema
class ConnectionLog(BaseSchemaWithId):
    job_id: int
    device_id: int
    log: str # The actual (redacted) log content
    timestamp: datetime
    log_type: Literal["connection_log"] = "connection_log"

# Combined Log Type (for mixed results)
CombinedLog = Union[JobLog, ConnectionLog]

# Paginated response models
PaginatedJobLogResponse = create_paginated_response(JobLog)
PaginatedConnectionLogResponse = create_paginated_response(ConnectionLog)
PaginatedCombinedLogResponse = create_paginated_response(CombinedLog)
