"""
Logging utilities for NetRaven.

This module provides functions for configuring and using loggers in the NetRaven application.
It supports console and file logging, log rotation, JSON structured logging, and sensitive data redaction.
"""

import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Default logging configuration
DEFAULT_CONSOLE_LOGGING = True
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LOGGING = True
DEFAULT_FILE_LEVEL = logging.DEBUG
DEFAULT_FILE_PATH = "logs/netraven.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5
DEFAULT_JSON_LOGGING = False
DEFAULT_JSON_FILE_PATH = "logs/netraven.json.log"
DEFAULT_REDACT_SENSITIVE = True
DEFAULT_SENSITIVE_PATTERNS = ["password", "secret", "key", "token", "auth"]

# Singleton logger configuration
_loggers = {}
_log_config = {
    "console": {
        "enabled": DEFAULT_CONSOLE_LOGGING,
        "level": DEFAULT_CONSOLE_LEVEL
    },
    "file": {
        "enabled": DEFAULT_FILE_LOGGING,
        "level": DEFAULT_FILE_LEVEL,
        "path": DEFAULT_FILE_PATH,
        "max_bytes": DEFAULT_MAX_BYTES,
        "backup_count": DEFAULT_BACKUP_COUNT
    },
    "json": {
        "enabled": DEFAULT_JSON_LOGGING,
        "path": DEFAULT_JSON_FILE_PATH
    },
    "sensitive_data": {
        "redact_enabled": DEFAULT_REDACT_SENSITIVE,
        "patterns": DEFAULT_SENSITIVE_PATTERNS
    }
}


class SensitiveFilter(logging.Filter):
    """
    Filter for redacting sensitive information in log messages.
    """
    
    def __init__(self, patterns: List[str]):
        """
        Initialize with patterns to redact.
        
        Args:
            patterns: List of string patterns to redact
        """
        super().__init__()
        self.patterns = patterns
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record, redacting sensitive information.
        
        Args:
            record: Log record to filter
            
        Returns:
            Always True to allow the record through, after modification
        """
        if isinstance(record.msg, str):
            for pattern in self.patterns:
                # Look for pattern in log message
                if pattern.lower() in record.msg.lower():
                    # Find the pattern and replace the value
                    parts = record.msg.split(pattern, 1)
                    if len(parts) > 1:
                        # Try to find a value to redact after the pattern
                        value_part = parts[1].strip()
                        if value_part.startswith('='):
                            value_part = value_part[1:].strip()
                            # Find the end of the value
                            if ' ' in value_part:
                                value_end = value_part.find(' ')
                                value = value_part[:value_end]
                                record.msg = record.msg.replace(value, "********")
                            else:
                                record.msg = record.msg.replace(value_part, "********")
                        elif value_part.startswith(':'):
                            value_part = value_part[1:].strip()
                            # Find the end of the value
                            if ' ' in value_part:
                                value_end = value_part.find(' ')
                                value = value_part[:value_end]
                                record.msg = record.msg.replace(value, "********")
                            else:
                                record.msg = record.msg.replace(value_part, "********")
        
        # Handle args - they could contain sensitive data too
        if record.args:
            args_list = list(record.args)
            for i, arg in enumerate(args_list):
                if isinstance(arg, str):
                    for pattern in self.patterns:
                        if pattern.lower() in arg.lower():
                            args_list[i] = "********"
            record.args = tuple(args_list)
        
        return True


class JsonFormatter(logging.Formatter):
    """
    Formatter for JSON-structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string representing the log record
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "lineno": record.lineno,
            "process": record.process
        }
        
        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(config: Dict[str, Any] = None) -> None:
    """
    Configure global logging settings for NetRaven.
    
    Args:
        config: Dictionary with logging configuration
    """
    global _log_config
    
    if config is None:
        return
    
    # Update configuration
    if "logging" in config:
        log_config = config["logging"]
        
        # Console logging settings
        if "console" in log_config:
            console_config = log_config["console"]
            if "enabled" in console_config:
                _log_config["console"]["enabled"] = console_config["enabled"]
            if "level" in console_config:
                level_name = console_config["level"]
                _log_config["console"]["level"] = getattr(logging, level_name.upper())
        
        # File logging settings
        if "file" in log_config:
            file_config = log_config["file"]
            if "enabled" in file_config:
                _log_config["file"]["enabled"] = file_config["enabled"]
            if "level" in file_config:
                level_name = file_config["level"]
                _log_config["file"]["level"] = getattr(logging, level_name.upper())
            if "filename" in file_config and "directory" in log_config:
                directory = log_config["directory"]
                filename = file_config["filename"]
                _log_config["file"]["path"] = os.path.join(directory, filename)
            if "max_size_mb" in file_config:
                _log_config["file"]["max_bytes"] = file_config["max_size_mb"] * 1024 * 1024
            if "backup_count" in file_config:
                _log_config["file"]["backup_count"] = file_config["backup_count"]
        
        # JSON logging settings
        if "json" in log_config:
            json_config = log_config["json"]
            if "enabled" in json_config:
                _log_config["json"]["enabled"] = json_config["enabled"]
            if "filename" in json_config and "directory" in log_config:
                directory = log_config["directory"]
                filename = json_config["filename"]
                _log_config["json"]["path"] = os.path.join(directory, filename)
        
        # Sensitive data settings
        if "sensitive_data" in log_config:
            sensitive_config = log_config["sensitive_data"]
            if "redact_enabled" in sensitive_config:
                _log_config["sensitive_data"]["redact_enabled"] = sensitive_config["redact_enabled"]
            if "patterns" in sensitive_config:
                _log_config["sensitive_data"]["patterns"] = sensitive_config["patterns"]


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the specified name.
    
    This function creates or returns a logger with handlers configured
    according to the application settings.
    
    Args:
        name: Logger name, typically the module name
        
    Returns:
        Configured logger instance
    """
    global _loggers
    
    # Return existing logger if already created
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to lowest level to catch all logs
    logger.propagate = False  # Don't propagate to root logger
    
    # Clean existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler if enabled
    if _log_config["console"]["enabled"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_log_config["console"]["level"])
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if _log_config["file"]["enabled"]:
        # Create logs directory if it doesn't exist
        log_path = _log_config["file"]["path"]
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=_log_config["file"]["max_bytes"],
            backupCount=_log_config["file"]["backup_count"]
        )
        file_handler.setLevel(_log_config["file"]["level"])
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Add JSON file handler if enabled
    if _log_config["json"]["enabled"]:
        # Create logs directory if it doesn't exist
        json_log_path = _log_config["json"]["path"]
        json_log_dir = os.path.dirname(json_log_path)
        if json_log_dir and not os.path.exists(json_log_dir):
            os.makedirs(json_log_dir, exist_ok=True)
        
        json_file_handler = logging.handlers.RotatingFileHandler(
            json_log_path,
            maxBytes=_log_config["file"]["max_bytes"],
            backupCount=_log_config["file"]["backup_count"]
        )
        json_file_handler.setLevel(_log_config["file"]["level"])
        json_formatter = JsonFormatter()
        json_file_handler.setFormatter(json_formatter)
        logger.addHandler(json_file_handler)
    
    # Add sensitive data filter if enabled
    if _log_config["sensitive_data"]["redact_enabled"]:
        sensitive_filter = SensitiveFilter(_log_config["sensitive_data"]["patterns"])
        logger.addFilter(sensitive_filter)
    
    # Store logger in cache
    _loggers[name] = logger
    
    return logger 