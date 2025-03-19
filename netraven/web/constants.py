"""
Constants and enums for the NetRaven web interface.

This module provides constants and enums used throughout the web interface.
"""

from enum import Enum

class JobTypeEnum(str, Enum):
    """Job type enum for scheduled jobs."""
    BACKUP = "backup"
    # Future job types can be added here

class ScheduleTypeEnum(str, Enum):
    """Schedule type enum for scheduled jobs."""
    IMMEDIATE = "immediate"
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly" 