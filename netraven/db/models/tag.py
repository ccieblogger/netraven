from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from netraven.db.base import Base

# Association table for Device <-> Tag
device_tag_association = Table(
    "device_tag_association",
    Base.metadata,
    Column("device_id", Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for Credential <-> Tag
credential_tag_association = Table(
    "credential_tag_association",
    Base.metadata,
    Column("credential_id", Integer, ForeignKey("credentials.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for Job <-> Tag
job_tags_association = Table(
    'job_tags', Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class Tag(Base):
    """Represents a tag that can be associated with Devices or Credentials.

    Tags provide a flexible way to group and categorize items.
    """
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(String)  # E.g., 'location', 'role', 'custom'

    devices = relationship(
        "Device",
        secondary=device_tag_association,
        back_populates="tags"
    )
    credentials = relationship(
        "Credential",
        secondary=credential_tag_association,
        back_populates="tags"
    )
    jobs = relationship(
        "Job",
        secondary=job_tags_association,
        back_populates="tags"
    ) 