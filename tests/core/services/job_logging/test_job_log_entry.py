"""
Tests for the JobLogEntry class.
"""

import pytest
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any

from netraven.core.services.job_logging_service import JobLogEntry


class TestJobLogEntry:
    """Test cases for the JobLogEntry class."""

    def test_initialization_minimal(self):
        """Test initialization with minimal parameters."""
        job_id = str(uuid.uuid4())
        message = "Test message"
        
        entry = JobLogEntry(job_id=job_id, message=message)
        
        assert entry.job_id == job_id
        assert entry.message == message
        assert entry.level == "INFO"  # Default level
        assert entry.category is None
        assert isinstance(entry.details, dict)
        assert len(entry.details) == 0
        assert entry.source_component is None
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.entry_id, str)

    def test_initialization_full(self):
        """Test initialization with all parameters specified."""
        job_id = str(uuid.uuid4())
        message = "Test message"
        level = "ERROR"
        category = "test_category"
        details = {"key": "value"}
        source = "test_component"
        timestamp = datetime.utcnow() - timedelta(hours=1)
        entry_id = str(uuid.uuid4())
        
        entry = JobLogEntry(
            job_id=job_id,
            message=message,
            level=level,
            category=category,
            details=details,
            source_component=source,
            timestamp=timestamp,
            entry_id=entry_id
        )
        
        assert entry.job_id == job_id
        assert entry.message == message
        assert entry.level == "ERROR"
        assert entry.category == category
        assert entry.details == details
        assert entry.source_component == source
        assert entry.timestamp == timestamp
        assert entry.entry_id == entry_id

    def test_level_capitalization(self):
        """Test that level is always stored in uppercase."""
        entry = JobLogEntry(job_id="test", message="test", level="debug")
        assert entry.level == "DEBUG"

        entry = JobLogEntry(job_id="test", message="test", level="ERROR")
        assert entry.level == "ERROR"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        job_id = "job-123"
        message = "Test message"
        level = "WARNING"
        category = "test_category"
        details = {"key": "value"}
        source = "test_component"
        timestamp = datetime.utcnow()
        entry_id = "entry-123"
        
        entry = JobLogEntry(
            job_id=job_id,
            message=message,
            level=level,
            category=category,
            details=details,
            source_component=source,
            timestamp=timestamp,
            entry_id=entry_id
        )
        
        entry_dict = entry.to_dict()
        
        assert entry_dict["id"] == entry_id
        assert entry_dict["job_id"] == job_id
        assert entry_dict["message"] == message
        assert entry_dict["level"] == level
        assert entry_dict["category"] == category
        assert entry_dict["details"] == details
        assert entry_dict["source_component"] == source
        assert entry_dict["timestamp"] == timestamp.isoformat()

    def test_from_dict_minimal(self):
        """Test creation from dictionary with minimal fields."""
        data = {
            "job_id": "job-123",
            "message": "Test message"
        }
        
        entry = JobLogEntry.from_dict(data)
        
        assert entry.job_id == data["job_id"]
        assert entry.message == data["message"]
        assert entry.level == "INFO"  # Default
        assert entry.category is None
        assert isinstance(entry.details, dict)
        assert len(entry.details) == 0
        assert entry.source_component is None
        assert isinstance(entry.timestamp, datetime)
        assert isinstance(entry.entry_id, str)

    def test_from_dict_full(self):
        """Test creation from dictionary with all fields."""
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.isoformat()
        
        data = {
            "id": "entry-123",
            "job_id": "job-123",
            "message": "Test message",
            "level": "ERROR",
            "category": "test_category",
            "details": {"key": "value"},
            "source_component": "test_component",
            "timestamp": timestamp_str
        }
        
        entry = JobLogEntry.from_dict(data)
        
        assert entry.entry_id == data["id"]
        assert entry.job_id == data["job_id"]
        assert entry.message == data["message"]
        assert entry.level == data["level"]
        assert entry.category == data["category"]
        assert entry.details == data["details"]
        assert entry.source_component == data["source_component"]
        assert entry.timestamp.isoformat() == timestamp_str

    def test_from_dict_invalid_timestamp(self):
        """Test handling of invalid timestamp in dictionary."""
        data = {
            "job_id": "job-123",
            "message": "Test message",
            "timestamp": "invalid-timestamp"
        }
        
        entry = JobLogEntry.from_dict(data)
        
        # Should create a new timestamp since the provided one is invalid
        assert isinstance(entry.timestamp, datetime)
        assert (datetime.utcnow() - entry.timestamp).total_seconds() < 5  # Should be recent 