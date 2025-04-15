from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from netraven.db.base import Base

class SystemSetting(Base):
    """Stores system-wide configuration settings in the database.
    
    This model provides a centralized, persistent store for application 
    configuration values that can be modified at runtime. Using the database
    for settings allows configuration changes without requiring application
    restarts or file modifications.
    
    Values are stored as JSONB for flexibility, allowing complex nested
    configuration objects to be stored and retrieved efficiently.
    
    Attributes:
        id: Primary key identifier for the setting
        key: Unique string identifier for the setting (used for lookups)
        value: The setting's value stored as JSONB (can be any valid JSON structure)
        description: Human-readable description of the setting's purpose
    """
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(JSONB, nullable=False)
    description = Column(String) 