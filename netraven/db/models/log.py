import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from netraven.db.base import Base

class LogType(enum.Enum):
    JOB = "job"
    CONNECTION = "connection"
    SESSION = "session"
    SYSTEM = "system"

class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class Log(Base):
    """Unified log model for all log events (job, connection, session, system, etc.)."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    log_type = Column(String(32), nullable=False, index=True)
    level = Column(String(16), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True, index=True)
    job_type_id = Column(Integer, ForeignKey("job_type.id"), nullable=True, index=True)
    source = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    meta = Column(JSONB, nullable=True)

    # Relationships (optional, for ORM navigation)
    job = relationship("Job", backref="logs", foreign_keys=[job_id])
    device = relationship("Device", backref="logs", foreign_keys=[device_id])

    __table_args__ = (
        Index("idx_logs_job_id", "job_id"),
        Index("idx_logs_device_id", "device_id"),
        Index("idx_logs_log_type", "log_type"),
        Index("idx_logs_level", "level"),
        Index("idx_logs_timestamp", "timestamp"),
        Index("idx_logs_job_type_id", "job_type_id"),
    ) 