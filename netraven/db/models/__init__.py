"""Database models for the NetRaven application.

This package contains SQLAlchemy ORM models that define the database schema
and relationships between entities in the NetRaven system. These models form
the core data structure of the application, representing network devices,
credentials, jobs, configurations, and their relationships.

The models use SQLAlchemy's declarative base pattern and include relationship
definitions that establish the connections between different entities.
"""

"""Database model imports for convenience."""

# Import all models for easier access
from netraven.db.models.device import Device
from netraven.db.models.job import Job
from netraven.db.models.log import Log, LogType, LogLevel
from netraven.db.models.job_status import JobStatus
from netraven.db.models.tag import Tag, device_tag_association, credential_tag_association, job_tags_association
#from netraven.db.models.job_log import JobLog, LogLevel  # Deprecated
#from netraven.db.models.connection_log import ConnectionLog  # Deprecated
from netraven.db.models.device_config import DeviceConfiguration
from netraven.db.models.credential import Credential
from netraven.db.models.system_setting import SystemSetting
from netraven.db.models.user import User

# These are all exported for convenience when importing from netraven.db.models
__all__ = [
    "Device", 
    "Job",
    "Log",
    "LogType",
    "LogLevel",
    "JobStatus",
    "Tag",
    "device_tag_association",
    "credential_tag_association",
    "job_tags_association",
    # "JobLog",  # Deprecated
    "DeviceConfiguration",
    "Credential",
    "SystemSetting",
    "User"
] 