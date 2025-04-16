"""API schema definitions for the NetRaven application.

This package contains Pydantic models that define the request and response
schemas for the NetRaven API. These models handle validation, serialization,
and documentation for the API endpoints.

Each module corresponds to a specific resource or domain within the application:
- device: Network device schemas
- credential: Authentication credential schemas
- job: Job execution schemas
- tag: Tag/categorization schemas
- user: User account schemas
- log: Log entry schemas
- token: Authentication token schemas
- base: Common base classes and utilities
"""

from . import device
from . import job
from . import user
from . import log
from . import token
from . import tag
from . import credential
from . import base
