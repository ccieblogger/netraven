from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from netraven_db.db.base import Base  # Assuming Base is in netraven_db.db.base

class ConnectionLog(Base):
    __tablename__ = 'connection_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"))
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    log = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now()) 