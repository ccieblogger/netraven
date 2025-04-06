from sqlalchemy import Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from netraven_db.db.base import Base
import datetime

# Association Table for Device <-> Tag Many-to-Many relationship
device_tag_association = Table(
    'device_tag_association',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('devices.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, unique=True, index=True, nullable=False)
    device_type = Column(String, index=True)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    configurations = relationship("DeviceConfiguration", back_populates="device", cascade="all, delete-orphan")
    tags = relationship(
        "Tag",
        secondary=device_tag_association,
        back_populates="devices"
    )
    jobs = relationship("Job", back_populates="device", cascade="all, delete-orphan") # Added relationship based on Job model FK 