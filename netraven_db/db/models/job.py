from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
import datetime

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete="SET NULL"), nullable=True) # Allow jobs to exist even if device is deleted
    status = Column(String, index=True, nullable=False, default='pending') # e.g., pending, running, completed, failed
    scheduled_for = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    device = relationship("Device", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan") 