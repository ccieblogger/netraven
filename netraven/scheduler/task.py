"""
Base class for scheduled tasks in NetRaven.

This module provides a base class for all scheduled tasks that can be 
executed by the scheduler.
"""

from typing import Dict, Optional, Any

class ScheduledTask:
    """Base class for scheduled tasks."""
    
    NAME = "base_task"
    DESCRIPTION = "Base scheduled task"
    
    def __init__(self, config=None):
        """Initialize the scheduled task."""
        self.config = config or {}
    
    def initialize(self):
        """Initialize the task resources."""
        return True
    
    def run(self):
        """Run the task."""
        raise NotImplementedError("Subclasses must implement the run method")
    
    def cleanup(self):
        """Clean up resources."""
        pass 