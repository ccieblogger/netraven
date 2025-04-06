from sqlalchemy import Column, Integer, String, JSON, Text
from netraven_db.db.base import Base

class SystemSetting(Base):
    __tablename__ = 'system_settings'

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    # Use JSON type for flexibility in storing different setting types (string, int, bool, list, dict)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True) 