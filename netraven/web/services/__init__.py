"""
Services for the NetRaven web interface.

This package contains service modules for the NetRaven web interface,
providing higher-level functionality that integrates multiple components.
"""

from netraven.web.services.scheduler_service import get_scheduler_service

__all__ = [
    'get_scheduler_service',
] 