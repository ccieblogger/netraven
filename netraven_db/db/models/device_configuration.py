from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
import datetime

class DeviceConfiguration(Base):
    __tablename__ = 'device_configurations'

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"), nullable=False)
    config_data = Column(Text, nullable=False)
    retrieved_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    metadata_ = Column('metadata', JSON) # Use metadata_ to avoid conflict with SQLAlchemy internal attribute

    # Relationships
    device = relationship("Device", back_populates="configurations") 