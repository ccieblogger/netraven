"""
Pydantic schemas for the NetRaven web interface.

This package contains Pydantic models that define the shape of request
and response data for the NetRaven API endpoints.
"""

# Import schemas to make them available when importing the package
from netraven.web.schemas import job_log
from netraven.web.schemas import scheduled_job 