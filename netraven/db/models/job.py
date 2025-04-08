from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship

from netraven.db.base import Base
from netraven.db.models.tag import job_tags_association

class Job(Base):
    """Represents a task to be performed, usually against a group of devices via Tags.

    Jobs are typically created and managed by the scheduler or API calls.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    status = Column(String, nullable=False, default="pending", index=True) # E.g., pending, running, completed, failed
    scheduled_for = Column(DateTime(timezone=True), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    is_enabled = Column(Boolean, default=True, index=True)
    schedule_type = Column(String)
    interval_seconds = Column(Integer)
    cron_string = Column(String)

    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")
    connection_logs = relationship("ConnectionLog", back_populates="job", cascade="all, delete-orphan")
    tags = relationship(
        "Tag",
        secondary=job_tags_association,
        back_populates="jobs"
    ) 