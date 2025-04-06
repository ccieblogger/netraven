from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from netraven.db.base import Base

class Job(Base):
    """Represents a task to be performed, usually involving a device.

    Jobs are typically created and managed by the scheduler or API calls.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    # device_id might be nullable if job applies to a group?
    # SOT implies one job per device for now.
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False, default="pending", index=True) # E.g., pending, running, completed, failed
    scheduled_for = Column(DateTime(timezone=True), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    # Consider adding job_type (e.g., 'backup', 'discovery')
    # Consider adding recurrence info if using db scheduler instead of RQ

    device = relationship("Device", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    connection_logs = relationship("ConnectionLog", back_populates="job", cascade="all, delete-orphan") 