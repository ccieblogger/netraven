from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from netraven.db.base import Base

class DeviceConfiguration(Base):
    __tablename__ = "device_configurations"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    config_data = Column(Text, nullable=False) # Stores the actual configuration text
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    metadata = Column(JSONB) # For storing commit hash, job ID, etc.

    device = relationship("Device", back_populates="configurations") 