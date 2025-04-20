import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship

from netraven.db.base import Base

class LogLevel(enum.Enum):
    """Enumeration of log severity levels for job logs.
    
    These levels follow standard logging severity conventions from lowest
    (DEBUG) to highest (CRITICAL) priority.
    
    Attributes:
        DEBUG: Detailed information for debugging purposes
        INFO: General informational messages about normal operation
        WARNING: Indication of a potential issue that doesn't prevent operation
        ERROR: Error condition that prevented a specific operation
        CRITICAL: Critical failure that stopped job execution
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class JobLog(Base):
    """Records a log message associated with a specific Job and Device.
    
    This model stores structured log entries generated during job execution,
    providing an audit trail and diagnostics for job execution. Logs can be
    associated with both a job and optionally a specific device.
    
    Attributes:
        id: Primary key identifier for the log entry
        job_id: Foreign key reference to the associated Job
        device_id: Optional foreign key reference to a specific Device
        message: The log message text
        level: Severity level of the log entry (from LogLevel enum)
        timestamp: When the log entry was created
        job: Relationship to the parent Job
        device: Optional relationship to the associated Device
    """
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    message = Column(String, nullable=False)
    level = Column(Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job = relationship("Job", back_populates="logs")
    device = relationship("Device") 