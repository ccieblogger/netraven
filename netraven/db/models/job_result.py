from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from netraven.db.base import Base

class JobResult(Base):
    """Represents the outcome of a job for a specific device."""
    __tablename__ = "job_results"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False)
    result_time = Column(DateTime(timezone=True), nullable=False)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    job = relationship("Job", backref="job_results")
    device = relationship("Device", backref="job_results") 