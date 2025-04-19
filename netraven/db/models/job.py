from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.orm import relationship

from netraven.db.base import Base
from netraven.db.models.tag import job_tags_association
from netraven.db.models.job_status import JobStatus

class Job(Base):
    """Represents a task to be performed, usually against a group of devices via Tags.

    This model defines automated or manual tasks that execute operations against
    network devices. Jobs can be one-time executions or scheduled recurring tasks
    that target devices via tag associations.
    
    Jobs are typically created and managed by the scheduler or API calls.
    
    Attributes:
        id: Primary key identifier for the job
        name: Human-readable name of the job
        job_type: Type of the job
        description: Detailed description of the job's purpose
        status: Current execution status (pending, running, completed, failed)
        scheduled_for: When the job is scheduled to run next
        started_at: When the job last started execution
        completed_at: When the job last finished execution
        is_enabled: Whether the job is active in the scheduler
        is_system_job: Whether the job is a system job
        schedule_type: Type of schedule (one-time, interval, cron)
        interval_seconds: For interval jobs, seconds between runs
        cron_string: For cron jobs, the cron expression defining the schedule
        logs: Related JobLog entries
        connection_logs: Related ConnectionLog entries
        tags: Tags associated with this job (for targeting devices)
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True, nullable=False)
    job_type = Column(String, nullable=False, default="backup", index=True)
    description = Column(String)
    status = Column(String, nullable=False, default=JobStatus.PENDING, index=True)
    scheduled_for = Column(DateTime(timezone=True), index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    is_enabled = Column(Boolean, default=True, index=True)
    is_system_job = Column(Boolean, default=False, index=True)
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