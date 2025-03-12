"""Tests for the logging utility module."""

import json
import logging
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.log_util import get_logger, SensitiveDataFilter, JSONFormatter

@pytest.fixture
def temp_log_file():
    """Fixture to create a temporary log file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        yield tmp.name
    try:
        os.unlink(tmp.name)
    except OSError:
        pass

def test_logger_creation():
    """Test basic logger creation."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"
    assert logger.level == logging.INFO

def test_logger_with_file(temp_log_file):
    """Test logger with file output."""
    logger = get_logger("test_file_logger", log_file=temp_log_file, json_format=True)
    test_message = "Test log message"
    logger.info(test_message)
    
    # Give async logging a moment to complete
    import time
    time.sleep(0.1)
    
    # Read the log file
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
    
    # Parse JSON content
    log_data = json.loads(log_content)
    assert log_data["message"] == test_message
    assert log_data["logger"] == "test_file_logger"
    assert log_data["level"] == "INFO"

def test_json_formatting():
    """Test JSON formatting of log messages."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    formatted = formatter.format(record)
    log_dict = json.loads(formatted)
    
    assert isinstance(log_dict, dict)
    assert log_dict["message"] == "Test message"
    assert log_dict["level"] == "INFO"
    assert log_dict["logger"] == "test_logger"

def test_sensitive_data_filtering():
    """Test filtering of sensitive data."""
    logger = get_logger("test_filter_logger")
    
    # Create a temporary handler to capture the output
    class CapturingHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []
        
        def emit(self, record):
            self.records.append(record)
    
    handler = CapturingHandler()
    logger.addHandler(handler)
    
    # Test sensitive data filtering
    sensitive_message = "token=secret123 password=mypass123"
    logger.info(sensitive_message)
    
    # Check if sensitive data was redacted
    assert "secret123" not in handler.records[0].msg
    assert "mypass123" not in handler.records[0].msg
    assert "token=*****" in handler.records[0].msg
    assert "password=*****" in handler.records[0].msg

def test_log_levels():
    """Test different log levels."""
    logger = get_logger("test_levels_logger", log_level="DEBUG")
    
    class CapturingHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []
        
        def emit(self, record):
            self.records.append(record)
    
    handler = CapturingHandler()
    logger.addHandler(handler)
    
    # Test all log levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    assert len(handler.records) == 5
    assert handler.records[0].levelname == "DEBUG"
    assert handler.records[1].levelname == "INFO"
    assert handler.records[2].levelname == "WARNING"
    assert handler.records[3].levelname == "ERROR"
    assert handler.records[4].levelname == "CRITICAL"

def test_exception_logging():
    """Test exception logging with stack trace."""
    logger = get_logger("test_exception_logger")
    
    class CapturingHandler(logging.Handler):
        def __init__(self):
            super().__init__()
            self.records = []
        
        def emit(self, record):
            self.records.append(record)
    
    handler = CapturingHandler()
    logger.addHandler(handler)
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("Error occurred", exc_info=True)
    
    # Check if exception info was captured
    assert len(handler.records) == 1
    assert handler.records[0].exc_info is not None
    formatted = JSONFormatter().format(handler.records[0])
    log_data = json.loads(formatted)
    assert log_data["error"] == "ValueError: Test exception"
    assert "Traceback" in log_data["exception"]

def test_async_logging(temp_log_file):
    """Test asynchronous logging."""
    logger = get_logger(
        "test_async_logger",
        log_file=temp_log_file,
        enable_async=True,
        json_format=True
    )
    
    # Log multiple messages
    for i in range(5):
        logger.info(f"Async test message {i}")
    
    # Give some time for async logging to complete
    import time
    time.sleep(0.1)
    
    # Check if messages were written to file
    with open(temp_log_file, 'r') as f:
        log_content = f.read()
        log_entries = [json.loads(line) for line in log_content.strip().split('\n')]
    
    assert len(log_entries) == 5
    for i, entry in enumerate(log_entries):
        assert entry["message"] == f"Async test message {i}"
        assert entry["logger"] == "test_async_logger"
        assert entry["level"] == "INFO"

if __name__ == "__main__":
    pytest.main([__file__]) 