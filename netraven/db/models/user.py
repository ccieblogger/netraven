from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, func, DateTime
from sqlalchemy.orm import relationship
from netraven.db.base import Base

class User(Base):
    """User model for NetRaven authentication and access control.
    
    This model manages user accounts for accessing the NetRaven system,
    including authentication information and role-based permissions.
    
    Attributes:
        id: Primary key identifier for the user
        username: Unique username for login
        email: Unique email address for the user
        hashed_password: Securely hashed password (never store plaintext)
        is_active: Whether the user account is currently active
        role: User's role determining permissions ("admin" or "user")
        full_name: Full name of the user
        created_at: Timestamp when the user account was created
        updated_at: Timestamp when the user account was last updated
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # Options: "admin", "user"
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships can be added here if needed
    # Example: jobs = relationship("Job", back_populates="user")