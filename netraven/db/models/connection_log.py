from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from netraven.db.base import Base

class ConnectionLog(Base):
    """Logs details about a specific connection attempt during a Job."""
    __tablename__ = 'connection_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    log = Column(Text, nullable=False) # Raw log from Netmiko/device interaction
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job = relationship("Job", back_populates="connection_logs")
    device = relationship("Device", back_populates="connection_logs") 