"""Logging utilities for worker operations.

This module provides functions for persisting various types of logs to the database.
It includes utilities for saving both connection logs (raw device interaction logs)
and job logs (structured event logs) for jobs and devices.

The logging functions manage database sessions and transactions appropriately,
handling both externally provided sessions and creating new sessions when needed.
"""

# All DB log utilities have been moved to netraven/db/log_utils.py
# If you need to save job or connection logs, import from netraven.db.log_utils
