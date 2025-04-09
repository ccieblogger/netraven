import pytest
import logging
from unittest.mock import Mock, patch
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    ConfigInvalidException,
    ReadTimeout,
    ConnectionException,
)
from git import GitCommandError

from netraven.worker.error_handler import (
    ErrorCategory,
    ErrorInfo,
    classify_exception,
    format_error_for_db
)

# --- Test ErrorInfo Class --- 

def test_error_info_init():
    """Test that ErrorInfo initializes with correct values."""
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Connection timed out",
        exception=Exception("Timeout test"),
        is_retriable=True,
        retry_count=1,
        max_retries=3,
        retry_delay=5,
        log_level=logging.WARNING,
        context={"job_id": 123, "device_id": 456}
    )
    
    assert error_info.category == ErrorCategory.TIMEOUT
    assert error_info.message == "Connection timed out"
    assert isinstance(error_info.exception, Exception)
    assert error_info.is_retriable is True
    assert error_info.retry_count == 1
    assert error_info.max_retries == 3
    assert error_info.retry_delay == 5
    assert error_info.log_level == logging.WARNING
    assert "job_id" in error_info.context
    assert error_info.context["job_id"] == 123
    assert "device_id" in error_info.context
    assert error_info.context["device_id"] == 456
    assert error_info.timestamp > 0  # Should be populated with current time

def test_should_retry():
    """Test should_retry logic."""
    # Should retry case
    retriable_error = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout",
        is_retriable=True,
        retry_count=1,
        max_retries=3
    )
    assert retriable_error.should_retry() is True
    
    # Should not retry - max retries reached
    max_retries_error = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout",
        is_retriable=True,
        retry_count=3,
        max_retries=3
    )
    assert max_retries_error.should_retry() is False
    
    # Should not retry - not retriable
    non_retriable_error = ErrorInfo(
        category=ErrorCategory.AUTHENTICATION,
        message="Auth failed",
        is_retriable=False,
        retry_count=0,
        max_retries=3
    )
    assert non_retriable_error.should_retry() is False

def test_next_retry_delay():
    """Test next_retry_delay with exponential backoff."""
    # Base case: initial delay
    error = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout",
        is_retriable=True,
        retry_count=0,
        max_retries=3,
        retry_delay=5
    )
    assert error.next_retry_delay() == 5  # Initial delay
    
    # Exponential backoff: 5 * 2^1 = 10
    error.retry_count = 1
    assert error.next_retry_delay() == 10
    
    # Exponential backoff: 5 * 2^2 = 20
    error.retry_count = 2
    assert error.next_retry_delay() == 20
    
    # No retry needed
    error.retry_count = 3
    assert error.next_retry_delay() == 0
    
    # Non-retriable error
    non_retriable = ErrorInfo(
        category=ErrorCategory.AUTHENTICATION,
        message="Auth failed",
        is_retriable=False,
        retry_delay=5
    )
    assert non_retriable.next_retry_delay() == 0

def test_increment_retry():
    """Test increment_retry creates new instance with incremented count."""
    original = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout",
        is_retriable=True,
        retry_count=1,
        max_retries=3,
        retry_delay=5,
        context={"job_id": 123}
    )
    
    new_error = original.increment_retry()
    
    # New object should be a different instance
    assert new_error is not original
    
    # All values should be the same except retry_count
    assert new_error.category == original.category
    assert new_error.message == original.message
    assert new_error.is_retriable == original.is_retriable
    assert new_error.max_retries == original.max_retries
    assert new_error.retry_delay == original.retry_delay
    assert new_error.context == original.context  # Check value equality
    assert new_error.context is not original.context  # Should be a copy
    
    # Retry count should be incremented
    assert new_error.retry_count == original.retry_count + 1

def test_to_dict():
    """Test conversion to dictionary for serialization."""
    exception = Exception("Test exception")
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout message",
        exception=exception,
        is_retriable=True,
        retry_count=1,
        max_retries=3,
        context={"job_id": 123}
    )
    
    result = error_info.to_dict()
    
    assert result["category"] == "TIMEOUT"
    assert result["message"] == "Timeout message"
    assert result["is_retriable"] is True
    assert result["retry_count"] == 1
    assert result["max_retries"] == 3
    assert "timestamp" in result
    assert result["exception_type"] == "Exception"
    assert result["exception_msg"] == "Test exception"
    assert "context" in result
    assert result["context"]["job_id"] == 123

def test_log(caplog):
    """Test logging functionality."""
    caplog.set_level(logging.WARNING)  # Set minimum level to capture
    
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout occurred",
        is_retriable=True,
        retry_count=1,
        max_retries=3,
        log_level=logging.WARNING
    )
    
    # Call the log method
    error_info.log()
    
    # Check that the log contains the message
    assert "TIMEOUT: Timeout occurred (Retry 2/3)" in caplog.text

# --- Test classify_exception --- 

def test_classify_netmiko_auth_exception():
    """Test classification of authentication exceptions."""
    ex = NetmikoAuthenticationException("Login failed")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.AUTHENTICATION
    assert "Authentication failed" in result.message
    assert result.is_retriable is False
    assert result.context["job_id"] == 123
    assert result.context["device_id"] == 456

def test_classify_netmiko_timeout_exception():
    """Test classification of timeout exceptions."""
    ex = NetmikoTimeoutException("Connection timed out")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.TIMEOUT
    assert "Connection timed out" in result.message
    assert result.is_retriable is True
    assert result.retry_count == 0
    assert result.max_retries > 0
    assert result.retry_delay > 0

def test_classify_command_timeout():
    """Test classification of command timeout exceptions."""
    ex = ReadTimeout("Command read timeout")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.COMMAND_TIMEOUT
    assert "Command execution timed out" in result.message
    assert result.is_retriable is True

def test_classify_invalid_command():
    """Test classification of invalid command exceptions."""
    ex = ConfigInvalidException("Invalid command syntax")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.COMMAND_SYNTAX
    assert "Invalid command" in result.message
    assert result.is_retriable is False

def test_classify_connection_refused():
    """Test classification of connection refused exceptions."""
    ex = ConnectionException("Connection refused")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.CONNECTION_REFUSED
    assert "Connection refused" in result.message
    assert result.is_retriable is True

def test_classify_git_exception():
    """Test classification of Git exceptions."""
    ex = GitCommandError(["git", "commit"], 128, "error: could not lock config file")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.CONFIG_SAVE_FAILURE
    assert "Git repository" in result.message
    assert result.is_retriable is True
    assert result.max_retries == 1  # Git errors have fewer retries

def test_classify_unknown_exception():
    """Test classification of unknown exceptions."""
    ex = ValueError("Some random error")
    result = classify_exception(ex, job_id=123, device_id=456)
    
    assert result.category == ErrorCategory.UNKNOWN
    assert "Unknown error" in result.message
    assert result.is_retriable is True

def test_classify_with_custom_retry_config():
    """Test error classification with custom retry configuration."""
    custom_config = {"max_retries": 5, "retry_delay": 10}
    ex = NetmikoTimeoutException("Connection timed out")
    
    result = classify_exception(ex, retry_config=custom_config)
    
    assert result.max_retries == 5
    assert result.retry_delay == 10

# --- Test format_error_for_db --- 

def test_format_error_for_db():
    """Test formatting errors for database storage."""
    exception = ValueError("Test error")
    error_info = ErrorInfo(
        category=ErrorCategory.TIMEOUT,
        message="Timeout message",
        exception=exception,
        is_retriable=True,
        retry_count=2,
        max_retries=3
    )
    
    result = format_error_for_db(error_info)
    
    assert result["error_category"] == "TIMEOUT"
    assert result["error_message"] == "Timeout message"
    assert result["is_retriable"] is True
    assert result["retry_count"] == 2
    assert result["retry_max"] == 3
    assert result["exception_type"] == "ValueError"
    assert result["exception_details"] == "Test error" 