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

# Configure logging
logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Classification for device connection and operation errors."""
    
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
    """Structured error information with retry guidance."""
    
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
        """Determine if another retry attempt should be made."""
        return self.is_retriable and self.retry_count < self.max_retries
    
    def next_retry_delay(self) -> int:
        """Calculate the next retry delay using exponential backoff."""
        if not self.is_retriable or self.retry_count >= self.max_retries:
            return 0
        
        # Simple exponential backoff: delay * (2^retry_count)
        return self.retry_delay * (2 ** self.retry_count)
    
    def increment_retry(self) -> 'ErrorInfo':
        """Create a new ErrorInfo with retry_count incremented."""
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
        """Convert to dictionary for logging and storage."""
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
        """Log the error with appropriate severity level."""
        logger_to_use = logger_instance or logger
        
        log_data = self.to_dict()
        # Remove 'message' key to avoid conflict with LogRecord
        if 'message' in log_data:
            log_data['error_message'] = log_data.pop('message')
            
        msg = f"{log_data['category']}: {self.message}"
        
        if self.is_retriable:
            msg += f" (Retry {self.retry_count+1}/{self.max_retries})"
            
        logger_to_use.log(self.log_level, msg, extra=log_data)


def classify_exception(
    ex: Exception, 
    job_id: Optional[int] = None,
    device_id: Optional[int] = None,
    retry_config: Optional[Dict[str, Any]] = None
) -> ErrorInfo:
    """
    Classify an exception into a structured error type with retry guidance.
    
    Args:
        ex: The exception to classify
        job_id: Optional job ID for context
        device_id: Optional device ID for context
        retry_config: Configuration for retries (attempts, delay)
    
    Returns:
        ErrorInfo with classification and retry information
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
    """
    Format an ErrorInfo object for storage in the database.
    
    Args:
        error_info: The error information to format
        
    Returns:
        Dictionary with formatted error information suitable for DB storage
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