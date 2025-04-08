from pydantic import Field
from datetime import datetime
from typing import Optional

from .base import BaseSchema, BaseSchemaWithId
from netraven.db.models.job_log import LogLevel # Import enum

# --- Log Schemas (JobLog & ConnectionLog) ---

# JobLog Read Schema
class JobLog(BaseSchemaWithId):
    job_id: int
    device_id: Optional[int] = None # Nullable as per model
    message: str
    level: LogLevel # Use the enum
    timestamp: datetime

# ConnectionLog Read Schema
class ConnectionLog(BaseSchemaWithId):
    job_id: int
    device_id: int
    log: str # The actual (redacted) log content
    timestamp: datetime
