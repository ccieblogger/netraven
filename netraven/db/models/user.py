from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from netraven.db.base import Base

class User(Base):
    """
    User model for NetRaven authentication and access control.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # Options: "admin", "user"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships can be added here if needed
    # Example: jobs = relationship("Job", back_populates="user") 