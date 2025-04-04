"""
SQLAlchemy models for the NetRaven web interface.

This package contains the ORM models that represent the database schema
for the NetRaven application.
"""

# Import all models to make them available when importing the package
from netraven.web.models.user import User
from netraven.web.models.device import Device
from netraven.web.models.backup import Backup
from netraven.web.models.tag import Tag, TagRule
from netraven.web.models.job_log import JobLog, JobLogEntry
from netraven.web.models.scheduled_job import ScheduledJob
from netraven.web.models.admin_settings import AdminSetting
from netraven.web.models.credential import Credential, CredentialTag

__all__ = [
    'User', 'Device', 'Backup', 'Tag', 'TagRule', 
    'JobLog', 'JobLogEntry', 'ScheduledJob', 'AdminSetting',
    'Credential', 'CredentialTag'
] 