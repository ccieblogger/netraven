"""Error classification and handling for device operations.

This module provides structured error handling for network device operations,
implementing a classification system for various types of failures that can
occur during device connections and command execution.

Key components:
- ErrorCategory: Enum defining different categories of errors
- ErrorInfo: Class containing structured error information with retry guidance
- classify_exception: Function to classify exceptions into appropriate error types
- format_error_for_db: Helper to format error information for database storage

The error handling system supports:
- Intelligent classification of exceptions by type and context
- Configurable retry policies with exponential backoff
- Structured error information for logging and reporting
- Context preservation for debugging and analysis

This system is used throughout the worker components to provide consistent
error handling and reporting across all device operations.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, Tuple, List
import logging
import time
from netmiko.exceptions import (
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    ConfigInvalidException,
    ReadTimeout,
    ConnectionException,
)
from netraven.utils.unified_logger import get_unified_logger

# Configure logging
logger = get_unified_logger()

class ErrorCategory(Enum):
    """Classification for device connection and operation errors.
    
    These categories group various failure modes to facilitate standardized
    error handling, reporting, and retry policies. Each category represents
    a specific class of errors that may occur during device operations.
    """
    
    # Connection errors
    AUTHENTICATION = auto()      # Credentials incorrect
    TIMEOUT = auto()             # Connection timed out
    CONNECTION_REFUSED = auto()  # Device actively refused connection
    UNREACHABLE = auto()         # Device not reachable on network
    
    # Command execution errors
    COMMAND_SYNTAX = auto()      # Command syntax was invalid
    COMMAND_REJECTED = auto()    # Command rejected by device policy
    COMMAND_TIMEOUT = auto()     # Command execution timed out
    
    # Device state errors
    DEVICE_BUSY = auto()         # Device busy, try again later
    PRIVILEGE_LEVEL = auto()     # Insufficient privilege level
    
    # General errors
    CONFIG_SAVE_FAILURE = auto() # Failed to save configuration to Git
    UNKNOWN = auto()             # Uncategorized error
    INTERNAL = auto()            # Internal system error

class ErrorInfo:
    """Structured error information with retry guidance.
    
    This class encapsulates all information about an error that occurred
    during a device operation, including its classification, whether it
    should be retried, and if so, with what parameters.
    
    It provides methods to determine if retry should be attempted,
    calculate appropriate backoff times, and format the error information
    for logging and storage.
    
    Attributes:
        category (ErrorCategory): The categorization of this error
        message (str): Human-readable error message
        exception (Optional[Exception]): The original exception if applicable
        is_retriable (bool): Whether this error should be retried
        retry_count (int): How many retry attempts have been made so far
        max_retries (int): Maximum number of retry attempts allowed
        retry_delay (int): Base delay in seconds between retry attempts
        log_level (int): Logging level to use when logging this error
        context (Dict[str, Any]): Additional contextual information
        timestamp (float): When the error occurred (time.time() value)
    """
    
    def __init__(
        self,
        category: ErrorCategory,
        message: str,
        exception: Optional[Exception] = None,
        is_retriable: bool = False,
        retry_count: int = 0,
        max_retries: int = 0,
        retry_delay: int = 0,
        log_level: int = logging.ERROR,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize a new ErrorInfo instance.
        
        Args:
            category: Classification category for this error
            message: Human-readable error message
            exception: Original exception that caused this error (if any)
            is_retriable: Whether this error should be retried
            retry_count: Current number of retry attempts made
            max_retries: Maximum number of retry attempts to allow
            retry_delay: Base delay in seconds between retry attempts
            log_level: Logging level for this error
            context: Additional context information (e.g., job_id, device_id)
        """
        self.category = category
        self.message = message
        self.exception = exception
        self.is_retriable = is_retriable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.log_level = log_level
        self.context = context or {}
        self.timestamp = time.time()
    
    def should_retry(self) -> bool:
        """Determine if another retry attempt should be made.
        
        Checks both that the error is marked as retriable and that
        the maximum number of retries has not been reached.
        
        Returns:
            bool: True if another retry should be attempted, False otherwise
        """
        return self.is_retriable and self.retry_count < self.max_retries
    
    def next_retry_delay(self) -> int:
        """Calculate the next retry delay using exponential backoff.
        
        Implements an exponential backoff strategy where each successive
        retry waits longer than the previous one, using the formula:
        delay = base_delay * (2^retry_count)
        
        Returns:
            int: Number of seconds to wait before the next retry attempt,
                 or 0 if no more retries should be attempted
        """
        if not self.is_retriable or self.retry_count >= self.max_retries:
            return 0
        
        # Simple exponential backoff: delay * (2^retry_count)
        return self.retry_delay * (2 ** self.retry_count)
    
    def increment_retry(self) -> 'ErrorInfo':
        """Create a new ErrorInfo with retry_count incremented.
        
        Creates a new instance with an incremented retry counter while
        preserving all other attributes, ensuring immutability.
        
        Returns:
            ErrorInfo: A new ErrorInfo instance with retry_count incremented
        """
        new_error = ErrorInfo(
            category=self.category,
            message=self.message,
            exception=self.exception,
            is_retriable=self.is_retriable,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            log_level=self.log_level,
            context=self.context.copy()
        )
        return new_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and storage.
        
        Creates a dictionary representation of this error information
        suitable for JSON serialization, logging, and database storage.
        
        Returns:
            Dict[str, Any]: Dictionary containing all relevant error information
        """
        result = {
            'category': self.category.name,
            'message': self.message,
            'is_retriable': self.is_retriable,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timestamp': self.timestamp,
        }
        
        if self.exception:
            result['exception_type'] = type(self.exception).__name__
            result['exception_msg'] = str(self.exception)
            
        # Include any additional context
        if self.context:
            result['context'] = self.context
            
        return result
    
    def log(self, logger_instance=None):
        """Log the error with appropriate severity level.
        
        Logs the error using either the provided logger instance or the
        module-level logger. Uses the error's configured log level and
        includes all relevant error information as structured data.
        
        Args:
            logger_instance: Optional logger to use instead of the module logger
        """
        # Use UnifiedLogger for error logging
        log_data = self.to_dict()
        msg = f"{log_data['category']}: {self.message}"
        if self.is_retriable:
            msg += f" (Retry {self.retry_count+1}/{self.max_retries})"
        # Extract job_id/device_id if present in context
        job_id = log_data.get('context', {}).get('job_id')
        device_id = log_data.get('context', {}).get('device_id')
        logger.log(
            msg,
            level=logging.getLevelName(self.log_level),
            destinations=["stdout", "db"],
            job_id=job_id,
            device_id=device_id,
            source="error_handler",
            extra=log_data,
        )


def classify_exception(
    ex: Exception, 
    job_id: Optional[int] = None,
    device_id: Optional[int] = None,
    retry_config: Optional[Dict[str, Any]] = None
) -> ErrorInfo:
    """Classify an exception into a structured error type with retry guidance.
    
    This function inspects exceptions raised during device operations and
    categorizes them into appropriate ErrorCategory types, determining whether
    they are retriable and setting appropriate retry parameters.
    
    The function handles common network operation exceptions like authentication
    failures, timeouts, and connection errors, as well as command execution issues.
    It also provides special handling for Git operations and other system-level errors.
    
    Args:
        ex (Exception): The exception to classify
        job_id (Optional[int]): Optional job ID for context
        device_id (Optional[int]): Optional device ID for context
        retry_config (Optional[Dict[str, Any]]): Configuration for retries:
                                               - max_retries: Maximum attempts
                                               - retry_delay: Base delay in seconds
    
    Returns:
        ErrorInfo: Structured error information with appropriate classification
                  and retry guidance
    """
    # Default retry configuration if not provided
    if retry_config is None:
        retry_config = {
            'max_retries': 2,
            'retry_delay': 5
        }
    
    # Set up context dictionary with job and device info
    context = {}
    if job_id is not None:
        context['job_id'] = job_id
    if device_id is not None:
        context['device_id'] = device_id
    
    # Classify netmiko-specific exceptions
    if isinstance(ex, NetmikoAuthenticationException):
        return ErrorInfo(
            category=ErrorCategory.AUTHENTICATION,
            message="Authentication failed. Check credentials.",
            exception=ex,
            is_retriable=False,  # Don't retry auth failures - credentials won't magically change
            context=context,
            log_level=logging.ERROR
        )
    
    elif isinstance(ex, NetmikoTimeoutException):
        return ErrorInfo(
            category=ErrorCategory.TIMEOUT,
            message="Connection timed out. Device may be unreachable.",
            exception=ex,
            is_retriable=True,  # Retry timeouts - might be temporary
            retry_count=0,
            max_retries=retry_config['max_retries'],
            retry_delay=retry_config['retry_delay'],
            context=context,
            log_level=logging.WARNING
        )
    
    elif isinstance(ex, ReadTimeout):
        return ErrorInfo(
            category=ErrorCategory.COMMAND_TIMEOUT,
            message="Command execution timed out.",
            exception=ex,
            is_retriable=True,  # Retry command timeouts
            retry_count=0,
            max_retries=retry_config['max_retries'],
            retry_delay=retry_config['retry_delay'],
            context=context,
            log_level=logging.WARNING
        )
    
    elif isinstance(ex, ConfigInvalidException):
        return ErrorInfo(
            category=ErrorCategory.COMMAND_SYNTAX,
            message="Invalid command or configuration syntax.",
            exception=ex,
            is_retriable=False,  # Don't retry syntax errors
            context=context,
            log_level=logging.ERROR
        )
    
    elif isinstance(ex, ConnectionException):
        return ErrorInfo(
            category=ErrorCategory.CONNECTION_REFUSED,
            message="Connection refused by device.",
            exception=ex,
            is_retriable=True,  # Retry connection refused - might be temporary
            retry_count=0,
            max_retries=retry_config['max_retries'],
            retry_delay=retry_config['retry_delay'],
            context=context,
            log_level=logging.WARNING
        )
    
    # Handle Git-related errors
    elif 'GitCommandError' in type(ex).__name__:
        return ErrorInfo(
            category=ErrorCategory.CONFIG_SAVE_FAILURE,
            message="Failed to save configuration to Git repository.",
            exception=ex,
            is_retriable=True,  # Retry Git operations
            retry_count=0,
            max_retries=1,  # Fewer retries for Git operations
            retry_delay=retry_config['retry_delay'],
            context=context,
            log_level=logging.ERROR
        )
    
    # Default case for unclassified exceptions
    return ErrorInfo(
        category=ErrorCategory.UNKNOWN,
        message=f"Unknown error: {str(ex)}",
        exception=ex,
        is_retriable=True,  # Cautiously retry unknown errors
        retry_count=0,
        max_retries=retry_config['max_retries'],
        retry_delay=retry_config['retry_delay'],
        context=context,
        log_level=logging.ERROR
    )


def format_error_for_db(error_info: ErrorInfo) -> Dict[str, Any]:
    """Format an ErrorInfo object for storage in the database.
    
    Converts the ErrorInfo object to a dictionary format suitable for
    database storage, with standardized field names.
    
    Args:
        error_info (ErrorInfo): The error information to format
        
    Returns:
        Dict[str, Any]: Dictionary with formatted error information suitable
                       for database storage with the following fields:
                       - error_category: Name of the error category
                       - error_message: Human-readable error message
                       - is_retriable: Whether this error can be retried
                       - retry_count: Number of retry attempts made
                       - retry_max: Maximum allowed retry attempts
                       - exception_type: Type of the original exception (if any)
                       - exception_details: String representation of the exception
    """
    result = {
        'error_category': error_info.category.name,
        'error_message': error_info.message,
        'is_retriable': error_info.is_retriable,
        'retry_count': error_info.retry_count,
        'retry_max': error_info.max_retries,
    }
    
    if error_info.exception:
        result['exception_type'] = type(error_info.exception).__name__
        result['exception_details'] = str(error_info.exception)
    
    return result 