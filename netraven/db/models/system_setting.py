from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from netraven.db.base import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, nullable=False, unique=True, index=True)
    value = Column(JSONB, nullable=False)
    description = Column(String) 