r"""
Logging utility module for NetRaven.

This module provides a comprehensive logging system with the following features:
- Console and file logging with customizable formatting
- Log rotation based on file size with configurable backup count
- JSON structured logging for machine-readable output
- Sensitive data redaction for security
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Asynchronous logging for improved performance
- Cloud logging service integration (optional AWS CloudWatch support)

Example:
    Basic usage (uses settings from config):
        >>> from utils.log_util import get_logger
        >>> logger = get_logger("my_app")
        >>> logger.info("Application started")

    Override settings:
        >>> logger = get_logger("my_app", log_level="DEBUG", log_file="custom.log")
        >>> logger.debug("Debug message")

For detailed documentation, see docs/logging.md
"""

import logging
import logging.handlers
import json
import queue
import threading
import re
from pathlib import Path
import os
import stat
from typing import Optional, Union, Dict, Any
from functools import partial
from datetime import datetime
import yaml

class SensitiveDataFilter(logging.Filter):
    """
    Filter for redacting sensitive data in log messages.
    
    This filter uses regular expressions to identify and redact sensitive information
    such as API tokens, passwords, and secrets from log messages.
    
    Attributes:
        patterns (dict): Dictionary of pattern names and their regex patterns
        compiled_patterns (dict): Dictionary of compiled regex patterns for performance

    Example:
        >>> filter = SensitiveDataFilter()
        >>> filter.patterns['api_key'] = r'api_key=([^&\\s]+)'
        >>> logger.addFilter(filter)
    """
    
    def __init__(self, patterns: dict = None):
        """
        Initialize the filter with optional custom patterns.
        
        Args:
            patterns (dict, optional): Dictionary of pattern names and regex patterns.
                                     Defaults to None, which uses built-in patterns.
        """
        super().__init__()
        # Predefined patterns if none provided
        default_patterns = {
            'token': r'token=([^\s]+)',
            'password': r'password=([^\s]+)',
            'secret': r'secret=([^\s]+)'
        }
        self.patterns = patterns or default_patterns
        
        # Compile patterns for better performance
        self.compiled_patterns = {}
        for key, pattern in self.patterns.items():
            # Ensure we're using the right pattern format
            self.compiled_patterns[key] = re.compile(pattern)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Redact sensitive data from log messages.
        
        Args:
            record (logging.LogRecord): The log record to filter

        Returns:
            bool: Always returns True to allow the record through
        """
        if isinstance(record.msg, str):
            msg = record.msg
            # For each pattern, replace any match with field_name=*****
            for key, compiled_pattern in self.compiled_patterns.items():
                # Extract field name from pattern (assumes pattern format like "field_name=...")
                field_name = key.split('_')[-1]  # Use last part of key as field name
                
                # For the specific token=value pattern format we're using
                if "=" in self.patterns[key]:
                    field_prefix = self.patterns[key].split('=')[0]
                    if '(' in field_prefix:
                        # If using capture groups like (token)=...
                        field_prefix = field_prefix.replace('(', '').replace(')', '')
                    
                    # Replace with field_name=*****
                    msg = compiled_pattern.sub(f"{field_prefix}=*****", msg)
            
            record.msg = msg
        return True

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON objects with the following fields:
    - timestamp: ISO format timestamp
    - level: Log level (DEBUG, INFO, etc.)
    - logger: Logger name
    - module: Source module name
    - function: Function name
    - line: Line number
    - message: Log message
    - stack_info: Stack trace (if available)
    - exception: Exception details (if available)
    - error: Formatted error message (if exception occurred)

    Example JSON output:
        {
            "timestamp": "2025-03-11T10:30:45.123456",
            "level": "ERROR",
            "logger": "my_app",
            "module": "processor",
            "function": "process_data",
            "line": 45,
            "message": "Failed to process data",
            "error": "ValueError: Invalid data format"
        }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as JSON.
        
        Args:
            record (logging.LogRecord): The log record to format

        Returns:
            str: JSON-formatted log entry
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        if hasattr(record, 'stack_info') and record.stack_info:
            log_data['stack_info'] = record.stack_info
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            # Add the exception type and message for easier testing
            exc_type = record.exc_info[0].__name__
            exc_msg = str(record.exc_info[1])
            log_data['error'] = f"{exc_type}: {exc_msg}"

        return json.dumps(log_data)

class AsyncQueueHandler(logging.handlers.QueueHandler):
    """
    Asynchronous queue handler for non-blocking logging.
    
    This handler queues log records for asynchronous processing, preventing
    logging operations from blocking the main application thread.
    
    The handler uses an unlimited queue size by default and includes
    error handling for queue overflow situations.

    Note:
        This handler should be used with a QueueListener for processing
        the queued log records.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record asynchronously.
        
        Args:
            record (logging.LogRecord): The log record to emit

        Note:
            If the queue is full, the record will be dropped and an error
            will be reported through handleError().
        """
        try:
            self.enqueue(record)
        except queue.Full:
            self.handleError(record)

def ensure_log_directory(log_path: Path) -> None:
    """
    Ensure the log directory exists and has proper permissions.
    
    Args:
        log_path (Path): Path to the log file
        
    This function:
    1. Creates the log directory if it doesn't exist
    2. Sets appropriate permissions (755 for directories, 644 for files)
    3. Handles any permission or access errors gracefully
    """
    try:
        # Create directory if it doesn't exist
        log_dir = log_path.parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set directory permissions to 755 (rwxr-xr-x)
        os.chmod(log_dir, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        
        # If log file exists, ensure it has proper permissions (644)
        if log_path.exists():
            os.chmod(log_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
    except OSError as e:
        print(f"Warning: Could not set proper permissions for log directory/file: {e}")
        # Continue anyway as the directory might still be usable

def _load_settings() -> Dict[str, Any]:
    """
    Load logging settings from the configuration file.
    
    Returns:
        Dict[str, Any]: Dictionary containing logging settings
    """
    try:
        # Try to load from config/settings.yaml first
        settings_path = Path(__file__).parent.parent.parent / 'config' / 'settings.yaml'
        print(f"Attempting to load settings from: {settings_path}")
        if settings_path.exists():
            print(f"Settings file exists at: {settings_path}")
            with open(settings_path) as f:
                settings = yaml.safe_load(f)
                logging_settings = settings.get('logging', {})
                print(f"Loaded logging settings: {logging_settings}")
                return logging_settings
        else:
            print(f"Settings file not found at: {settings_path}")
    except Exception as e:
        print(f"Warning: Could not load logging settings: {e}")
    
    # Return default settings if loading fails
    default_settings = {
        'level': 'INFO',
        'format': 'json',
        'console': {
            'enabled': True,
            'level': 'INFO'
        },
        'file': {
            'enabled': True,
            'path': 'logs/netraven.log',
            'max_size_mb': 10,
            'backup_count': 5,
            'level': 'DEBUG'
        },
        'async_logging': True
    }
    print(f"Using default settings: {default_settings}")
    return default_settings

def get_logger(
    name: str,
    log_level: Optional[str] = None,
    log_file: Optional[Union[str, Path]] = None,
    json_format: Optional[bool] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    enable_console: Optional[bool] = None,
    enable_async: Optional[bool] = None,
    cloudwatch_config: Optional[Dict[str, Any]] = None
) -> logging.Logger:
    """
    Initialize and configure a logger with settings from config file and optional overrides.
    
    This function first loads settings from config/settings.yaml, then applies any
    provided overrides. This allows for consistent logging configuration across the
    application while maintaining flexibility when needed.

    Args:
        name: Logger name (should be unique and descriptive)
        log_level: Override default log level from settings
        log_file: Override default log file path from settings
        json_format: Override default format setting
        max_bytes: Override default max file size
        backup_count: Override default number of backup files
        enable_console: Override console logging setting
        enable_async: Override async logging setting
        cloudwatch_config: AWS CloudWatch configuration (optional)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Load settings from config file
    settings = _load_settings()
    
    # Apply settings with overrides
    log_level = log_level or settings.get('level', 'INFO')
    json_format = json_format if json_format is not None else settings.get('format') == 'json'
    
    file_config = settings.get('file', {})
    enable_file = file_config.get('enabled', True) if log_file is None else True
    log_file = log_file or file_config.get('path', 'logs/netraven.log')
    max_bytes = max_bytes or file_config.get('max_size_mb', 10) * 1024 * 1024
    backup_count = backup_count or file_config.get('backup_count', 5)
    
    console_config = settings.get('console', {})
    enable_console = enable_console if enable_console is not None else console_config.get('enabled', True)
    
    enable_async = enable_async if enable_async is not None else settings.get('async_logging', True)
    
    print(f"Configuring logger '{name}' with:")
    print(f"  - Log level: {log_level}")
    print(f"  - Log file: {log_file}")
    print(f"  - JSON format: {json_format}")
    print(f"  - Enable file: {enable_file}")
    print(f"  - Enable console: {enable_console}")
    print(f"  - Enable async: {enable_async}")
    
    # Initialize logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove any existing handlers
    logger.handlers = []

    # Create formatters
    json_formatter = JSONFormatter()
    standard_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    formatter = json_formatter if json_format else standard_formatter

    handlers = []
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, console_config.get('level', 'INFO').upper()))
        handlers.append(console_handler)

    # File handler with rotation
    if enable_file:
        log_path = Path(log_file)
        print(f"Setting up file handler for: {log_path}")
        
        # Ensure log directory exists with proper permissions
        ensure_log_directory(log_path)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            delay=True  # Don't create file until first write
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, file_config.get('level', 'DEBUG').upper()))
        handlers.append(file_handler)
        print(f"Added file handler for: {log_path}")

    # CloudWatch handler (if configured)
    cloudwatch_config = cloudwatch_config or settings.get('cloudwatch', {})
    if cloudwatch_config.get('enabled', False):
        try:
            import watchtower
            cloudwatch_handler = watchtower.CloudWatchLogHandler(**cloudwatch_config)
            cloudwatch_handler.setFormatter(formatter)
            handlers.append(cloudwatch_handler)
        except ImportError:
            logger.warning("watchtower package not installed. CloudWatch logging disabled.")

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter(
        patterns=settings.get('sensitive_patterns', None)
    )
    
    # Set up queue for async logging
    if enable_async:
        log_queue = queue.Queue(-1)  # No limit on size
        queue_handler = AsyncQueueHandler(log_queue)
        queue_handler.addFilter(sensitive_filter)
        
        # Create and start listener
        queue_listener = logging.handlers.QueueListener(
            log_queue,
            *handlers,
            respect_handler_level=True
        )
        queue_listener.start()
        
        logger.addHandler(queue_handler)
    else:
        for handler in handlers:
            handler.addFilter(sensitive_filter)
            logger.addHandler(handler)

    return logger

# Example usage
if __name__ == "__main__":
    # Basic usage
    logger = get_logger(
        "netraven",
        log_level="DEBUG",
        log_file="logs/app.log",
        json_format=True
    )
    
    # Example logs
    logger.debug("Debug message")
    logger.info("Info message with sensitive data: token=secret123")
    logger.warning("Warning message")
    
    try:
        raise ValueError("Example error")
    except Exception as e:
        logger.error("Error occurred", exc_info=True) 