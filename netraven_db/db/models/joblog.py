from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
import datetime

class JobLog(Base):
    __tablename__ = 'job_logs'

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete="CASCADE"), nullable=False)
    message = Column(Text, nullable=False)
    level = Column(String, index=True, nullable=False) # e.g., INFO, WARNING, ERROR
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)

    # Relationships
    job = relationship("Job", back_populates="logs") 