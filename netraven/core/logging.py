"""
Logging utilities for NetRaven.

This module provides functions for configuring and using loggers in the NetRaven application.
It supports console and file logging, log rotation, JSON structured logging, and sensitive data redaction.
It also provides component-specific logging for frontend, backend, jobs, and authentication.
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
DEFAULT_JSON_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_JSON_BACKUP_COUNT = 5
DEFAULT_REDACT_SENSITIVE = True
DEFAULT_SENSITIVE_PATTERNS = ["password", "secret", "key", "token", "auth"]
DEFAULT_ROTATION_WHEN = None  # No time-based rotation by default
DEFAULT_ROTATION_INTERVAL = 1  # Default interval for time-based rotation

# Component-specific log files
COMPONENT_LOG_FILES = {
    "frontend": "logs/frontend.log",
    "backend": "logs/backend.log",
    "jobs": "logs/jobs.log",
    "auth": "logs/auth.log"
}

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
        "backup_count": DEFAULT_BACKUP_COUNT,
        "rotation_when": DEFAULT_ROTATION_WHEN,
        "rotation_interval": DEFAULT_ROTATION_INTERVAL
    },
    "json": {
        "enabled": DEFAULT_JSON_LOGGING,
        "path": DEFAULT_JSON_FILE_PATH,
        "max_bytes": DEFAULT_JSON_MAX_BYTES,
        "backup_count": DEFAULT_JSON_BACKUP_COUNT,
        "rotation_when": DEFAULT_ROTATION_WHEN,
        "rotation_interval": DEFAULT_ROTATION_INTERVAL
    },
    "sensitive_data": {
        "redact_enabled": DEFAULT_REDACT_SENSITIVE,
        "patterns": DEFAULT_SENSITIVE_PATTERNS
    },
    "components": {
        "enabled": True,
        "files": COMPONENT_LOG_FILES,
        "level": DEFAULT_FILE_LEVEL,
        "max_bytes": DEFAULT_MAX_BYTES,
        "backup_count": DEFAULT_BACKUP_COUNT,
        "rotation_when": DEFAULT_ROTATION_WHEN,
        "rotation_interval": DEFAULT_ROTATION_INTERVAL
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


class ComponentFilter(logging.Filter):
    """
    Filter to route log messages to component-specific log files.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize with the component name to filter for.
        
        Args:
            component_name: Name of the component to filter for
        """
        super().__init__()
        self.component_name = component_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record based on component name in the logger name.
        
        Args:
            record: Log record to filter
            
        Returns:
            True if the record belongs to this component, False otherwise
        """
        if self.component_name == "frontend" and "frontend" in record.name:
            return True
        elif self.component_name == "backend" and any(x in record.name for x in ["backend", "api", "web"]) and "auth" not in record.name:
            return True
        elif self.component_name == "jobs" and any(x in record.name for x in ["jobs", "device_comm", "backup"]):
            return True
        elif self.component_name == "auth" and "auth" in record.name:
            return True
        return False


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
            if "rotation_when" in file_config:
                _log_config["file"]["rotation_when"] = file_config["rotation_when"]
            if "rotation_interval" in file_config:
                _log_config["file"]["rotation_interval"] = file_config["rotation_interval"]
        
        # JSON logging settings
        if "json" in log_config:
            json_config = log_config["json"]
            if "enabled" in json_config:
                _log_config["json"]["enabled"] = json_config["enabled"]
            if "filename" in json_config and "directory" in log_config:
                directory = log_config["directory"]
                filename = json_config["filename"]
                _log_config["json"]["path"] = os.path.join(directory, filename)
            if "max_size_mb" in json_config:
                _log_config["json"]["max_bytes"] = json_config["max_size_mb"] * 1024 * 1024
            if "backup_count" in json_config:
                _log_config["json"]["backup_count"] = json_config["backup_count"]
            if "rotation_when" in json_config:
                _log_config["json"]["rotation_when"] = json_config["rotation_when"]
            if "rotation_interval" in json_config:
                _log_config["json"]["rotation_interval"] = json_config["rotation_interval"]
        
        # Sensitive data settings
        if "sensitive_data" in log_config:
            sensitive_config = log_config["sensitive_data"]
            if "redact_enabled" in sensitive_config:
                _log_config["sensitive_data"]["redact_enabled"] = sensitive_config["redact_enabled"]
            if "patterns" in sensitive_config:
                _log_config["sensitive_data"]["patterns"] = sensitive_config["patterns"]
        
        # Component logging settings
        if "components" in log_config:
            component_config = log_config["components"]
            if "enabled" in component_config:
                _log_config["components"]["enabled"] = component_config["enabled"]
            if "level" in component_config:
                level_name = component_config["level"]
                _log_config["components"]["level"] = getattr(logging, level_name.upper())
            if "files" in component_config:
                _log_config["components"]["files"].update(component_config["files"])
            if "max_size_mb" in component_config:
                _log_config["components"]["max_bytes"] = component_config["max_size_mb"] * 1024 * 1024
            if "backup_count" in component_config:
                _log_config["components"]["backup_count"] = component_config["backup_count"]
            if "rotation_when" in component_config:
                _log_config["components"]["rotation_when"] = component_config["rotation_when"]
            if "rotation_interval" in component_config:
                _log_config["components"]["rotation_interval"] = component_config["rotation_interval"]

    # Ensure log directories exist
    _ensure_log_directories()


def _ensure_log_directories() -> None:
    """
    Ensure all log directories exist with proper permissions.
    
    This function creates the necessary log directories if they don't exist
    and sets appropriate permissions to ensure all users can write to the logs.
    """
    # Main log file directory
    log_dir = os.path.dirname(_log_config["file"]["path"])
    os.makedirs(log_dir, exist_ok=True)
    try:
        # Try to set directory permissions to allow anyone to write logs
        os.chmod(log_dir, 0o777)
    except PermissionError:
        pass
    
    # Ensure main log file exists and is writable
    log_file = _log_config["file"]["path"]
    if not os.path.exists(log_file):
        try:
            # Create the file if it doesn't exist
            with open(log_file, 'w') as f:
                pass
            # Try to make the file writable by all
            os.chmod(log_file, 0o666)
        except (PermissionError, FileNotFoundError):
            pass
    
    # JSON log file directory
    json_log_dir = os.path.dirname(_log_config["json"]["path"])
    os.makedirs(json_log_dir, exist_ok=True)
    try:
        os.chmod(json_log_dir, 0o777)
    except PermissionError:
        pass
    
    # Ensure JSON log file exists and is writable
    json_log_file = _log_config["json"]["path"]
    if not os.path.exists(json_log_file):
        try:
            with open(json_log_file, 'w') as f:
                pass
            os.chmod(json_log_file, 0o666)
        except (PermissionError, FileNotFoundError):
            pass
    
    # Component log directories and files
    for component, log_path in _log_config["components"]["files"].items():
        # Get the full path
        full_path = os.path.join(log_dir, log_path)
        component_log_dir = os.path.dirname(full_path)
        
        # Create directory
        os.makedirs(component_log_dir, exist_ok=True)
        try:
            os.chmod(component_log_dir, 0o777)
        except PermissionError:
            pass
        
        # Create file if it doesn't exist
        if not os.path.exists(full_path):
            try:
                with open(full_path, 'w') as f:
                    pass
                os.chmod(full_path, 0o666)
            except (PermissionError, FileNotFoundError):
                pass


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Set the log level to DEBUG for development
    logger.setLevel(logging.DEBUG)
    
    # Add a console handler if not already present
    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 