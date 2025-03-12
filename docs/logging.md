# Logging Utility Documentation

## Overview
The logging utility provides a centralized, configurable logging system for the Netbox Updater application. It implements best practices for production-grade logging with features like structured JSON output, sensitive data redaction, asynchronous logging, log rotation, and session tracking.

## Features
- **Session Tracking**: Unique session IDs for tracking script executions
- **Connection Lifecycle Logging**: Complete tracking of device connections and disconnections
- **Structured JSON Logging**: All logs can be output in JSON format for easy parsing and analysis
- **Multiple Output Destinations**: Supports console, file, and AWS CloudWatch logging
- **Log Rotation**: Automatic rotation of log files based on size with configurable backup count
- **Sensitive Data Protection**: Automatic redaction of sensitive information like passwords and tokens
- **Asynchronous Logging**: Non-blocking logging operations for better performance
- **Multiple Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, and CRITICAL levels
- **Exception Tracking**: Comprehensive exception logging with stack traces
- **Cloud Integration**: Optional AWS CloudWatch integration for cloud-based log aggregation

## Usage Examples

### Basic Usage with Session Tracking
```python
import uuid
from src.utils.log_util import get_logger

# Generate a unique session ID
session_id = str(uuid.uuid4())

# Create a basic logger
logger = get_logger("my_application")

# Log messages with session context
logger.info(f"[Session: {session_id}] Application started")
logger.debug(f"[Session: {session_id}] Processing configuration")
```

### Device Connection Logging
```python
# Log the complete connection lifecycle
logger.debug(f"[Session: {session_id}] Attempting to connect to device {host}")
try:
    with device:
        if device.is_connected:
            logger.info(f"[Session: {session_id}] Successfully connected to {host}")
            # ... device operations ...
        else:
            logger.error(f"[Session: {session_id}] Failed to connect to {host}")
        # Disconnect logging handled automatically
        logger.info(f"[Session: {session_id}] Disconnected from {host}")
except Exception as e:
    logger.error(f"[Session: {session_id}] Connection error: {str(e)}")
```

### File Logging with Rotation
```python
logger = get_logger(
    name="my_application",
    log_file="logs/app.log",
    max_bytes=10_485_760,  # 10MB
    backup_count=5
)
```

### JSON Structured Logging
```python
logger = get_logger(
    name="my_application",
    json_format=True
)

# Output will be JSON formatted:
# {
#     "timestamp": "2025-03-11T10:30:45.123456",
#     "level": "INFO",
#     "logger": "my_application",
#     "module": "main",
#     "function": "process_config",
#     "line": 45,
#     "message": "Processing configuration"
# }
```

### Sensitive Data Handling
```python
logger = get_logger("my_application")

# Sensitive data will be automatically redacted
logger.info("API token=secret123")  # Will log: "API token=*****"
logger.info("password=mypassword")  # Will log: "password=*****"
```

### Exception Logging
```python
logger = get_logger("my_application")

try:
    raise ValueError("Something went wrong")
except Exception as e:
    logger.error("Error processing request", exc_info=True)
    # Will include full stack trace and exception details in JSON format
```

### AWS CloudWatch Integration
```python
cloudwatch_config = {
    "aws_region": "us-west-2",
    "log_group": "my-application",
    "log_stream": "app-logs"
}

logger = get_logger(
    name="my_application",
    cloudwatch_config=cloudwatch_config
)
```

## Configuration Options

### get_logger Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| name | str | Required | The name of the logger |
| log_level | str | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| log_file | str/Path | None | Path to log file (optional) |
| json_format | bool | True | Whether to use JSON formatting |
| max_bytes | int | 10MB | Maximum size of log file before rotation |
| backup_count | int | 5 | Number of backup files to keep |
| enable_console | bool | True | Whether to enable console logging |
| enable_async | bool | True | Whether to enable asynchronous logging |
| cloudwatch_config | dict | None | AWS CloudWatch configuration (optional) |

### Log Message Format
Standard JSON log entry includes:
```json
{
    "timestamp": "2025-03-11T10:30:45.123456",
    "level": "INFO",
    "logger": "device_test",
    "module": "device_test",
    "function": "connect_to_device",
    "line": 45,
    "message": "[Session: 3076f465-f8d8-4bd3-9bac-0d7e9e9dbc07] Successfully connected to 192.168.1.41"
}
```

### Sensitive Data Patterns
The following patterns are automatically redacted:
- API tokens: `token=value` or `token: value`
- Passwords: `password=value` or `password: value`
- Secrets: `secret=value` or `secret: value`

Custom patterns can be added by extending the `SensitiveDataFilter` class.

## Best Practices

1. **Session Management**:
   - Generate unique session IDs for each script execution
   - Include session ID in all relevant log messages
   - Track complete connection lifecycles

2. **Logger Naming**:
   - Use hierarchical names (e.g., "app.module.submodule")
   - Keep names consistent across the application

3. **Log Levels**:
   - DEBUG: Detailed information for debugging (connection attempts, detailed operations)
   - INFO: General operational information (successful connections, operations)
   - WARNING: Warning messages for potentially problematic situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical errors that may cause program failure

4. **Performance**:
   - Use async logging for high-throughput applications
   - Enable JSON formatting only when needed
   - Configure appropriate log rotation settings (default: 10MB, 5 backups)

5. **Security**:
   - Never log sensitive data
   - Use appropriate file permissions for log files
   - Regularly rotate and archive logs

## Implementation Details

### JSONFormatter
Custom formatter that produces structured JSON output including:
- Timestamp (ISO format)
- Log level
- Logger name
- Module name
- Function name
- Line number
- Message
- Stack trace (if applicable)
- Exception details (if applicable)

### AsyncQueueHandler
Non-blocking handler that queues log records for asynchronous processing:
- Uses a queue to store log records
- Processes records in a separate thread
- Handles queue overflow gracefully

### SensitiveDataFilter
Filter that redacts sensitive information:
- Uses regex patterns to identify sensitive data
- Replaces sensitive values with "*****"
- Compiled patterns for better performance

## Testing
The logging utility includes comprehensive tests covering:
- Basic logging functionality
- File output and rotation
- JSON formatting
- Sensitive data redaction
- Exception handling
- Asynchronous logging

Run tests using:
```bash
python -m pytest tests/test_log_util.py -v
``` 