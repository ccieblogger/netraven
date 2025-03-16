# Project Specification: NetRaven

## Project Overview
- **Project Name**: NetRaven
- **Description**: Python project to backup network device running configurations to multiple storage destinations, including local Git repositories 
                   and AWS S3 storage, with comprehensive version control and logging capabilities.
- **Author(s)**: Brian Larson
- **Date**: 03/10/2025

## Objectives
- Develop a Python application that does the following:
  1. Network device backup service:
     - Securely retrieves Cisco network device running configurations
     - Supports multiple storage destinations:
       a. Local Git repository with remote repository integration
       b. AWS S3 storage for cloud backup
     - Implements version control for configuration tracking
     - Provides comprehensive logging and error handling
     - Supports flexible configuration of backup schedules and storage options

## Requirements
### Functional Requirements
- Support secure retrieval of device configurations using industry-standard protocols
- Implement multiple storage backends (Git and AWS S3)
- Provide flexible configuration options for storage destinations
- Support scheduled and on-demand backups
- Implement robust error handling and retry mechanisms
- Maintain comprehensive logging of all operations
- Support configuration of device lists and credentials

### Non-Functional Requirements
- Ensure the tool is performant and can handle large configuration files.
- Maintain compatibility with Python 3.8+.
- Securely handle sensitive information such as Netbox API tokens.
- Provide clear and comprehensive documentation for users and developers.
- Implement a well-structured environment and organize code and configuration
  according to best practices.

## Technical Specifications
### Programming Language
- Python 3.10+ (strict requirement)

### Libraries and Frameworks
- `netmiko>=4.3.0` for interacting with Cisco devices (if needed)
- `textfsm>=1.1.3` for configuration file parsing to structure data
- `pynetbox>=7.3.2` for making API calls to Netbox and device inventory
- `pyyaml>=6.0.1` for handling configuration files and storing structured data
- `argparse>=1.4.0` for CLI implementation
- `logging` for logging and error handling


### Environment Setup
- Operating System: Ubuntu 22.04 LTS
- IDE/Editor: VS Code/Cursor
- Version Control: Git with GitHub repository (https://github.com/ccieblogger/netraven.git)

## Testing and Quality Assurance
- minimal testing is needed as this is a single person project
- test data will be stored in the tests directory

Network Device Communication Utility:
- Uses the Netmiko library to communicate to network devices though other methods may be added later as needed.
- provides a reusable connection function or class that:
- Connects to a remote network device using connection libraries provide by the connection libary (Currently only supports Netmiko)
- Provides methods to connect and disconnect to the device via support methods (SSH is the default)
- Credentials and connection information can be passed to the utility or pulled from settings
- should support the follow properties and methods
  - connect()
    - Method to connect via support protocol to interact with device.
    - Returns True is successful, false if not along with error
    - sets the IsConnected property to True
  - disconnect()
    - Method to disconnect to the device
    - This should always be called when when finished even if an error is encountered if a successfuly connection was already made.
    - Returns True is successful, false if not along with error
    - Sets the IsConnected property to False
  - IsConnected
    - A property that can be checked if the module is succesfully connected to the device
    - Ret
  - GetRunning
    - Should run appropriate methods or action to retrieve the running configuration from the device.
    - Should return raw text retrieved the device
  - GetSerial
    - perform action to retrieve the devices serial number
    - should return the raw text of the device
  - GetOS
    - perform action to retrieve the devices operating sytem and version
    - should return the raw text of the device
 Error Handling:
 - should confirm reachability and handle timeouts using a the subprocess system module
   - implement reusable function for this feature which returns a result and logs errors
 - errors that prevent connecting should be logged and the module should return a failure code to notify upstream processes.
 - All netmiko connection parameters should be supported
 - basic validation of connection parameters should be done.
   - Any missing required paramaters return an error
   - malformed paramaters also return error
   - optional paramaters should provide defaults which should be defined in the settings file and configurable by user.
 Device Support:
 Initial device support should include:
 - All devices supported by Netmiko
 Authentication:
 - should support password and key-based with password being the default
 - should support trying multiple passwords if provided or configured in settings.







Logging Utility Requirements:
- Use Python's logging module instead of print() for structured logging.
- Create a reusable logger function or class that:
  - Supports logging to both console and file.
  - Uses a module-specific logger instead of basicConfig().
  - Supports log rotation to prevent large log files (10MB max size, 5 backup files).
  - Support multiple log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
  - Enable JSON-based structured logging for machine-readable logs.
  - Ensure logs are written asynchronously to avoid blocking I/O operations.
  - Implement sensitive data redaction (e.g., passwords, API keys).
  - Allow optional integration with cloud logging services like AWS CloudWatch.
  - Capture full exception stack traces in logs for debugging.
  - Optimize performance for high-load applications (e.g., QueueHandler for multiprocessing).
  - Track script executions with unique session IDs.
  - Monitor complete connection lifecycles (connect, operations, disconnect).
  - Include contextual information in log messages (session ID, operation details).

Expected Output:
  A Python module or class (log_util.py) that provides a get_logger() function to initialize a logger.
  Example usage:
    session_id = str(uuid.uuid4())
    logger = get_logger("my_app")
    logger.info(f"[Session: {session_id}] Application started successfully")
  Ensure that all handlers and formatters are properly configured.

Additional Notes:
- Use a configurable approach so users can modify log levels and destinations easily.
- Provide a simple usage example demonstrating log rotation, JSON logging, session tracking, and error handling.
- Generate well-structured, production-ready code with comments explaining each part.
- Implement proper log rotation to manage file sizes and maintain history.
- Include session context in all relevant log messages for better traceability.
- Ensure complete lifecycle logging for critical operations.

Project Structure
    project_root/
    ├── src/           # Source code
    ├── tests/         # Test files and test data
    ├── logs/         # Application logs
    ├── config/       # Configuration files
    │   ├── settings.yaml
    │   └── credentials.yaml
    └── docs/         # Documentation and project specifications

## Documentation
- Include documentation of what the systems does and how to use and deploy it.

## References
  Before providing Python code, check the latest official documentation from:
  - pynetbox:
    - https://github.com/netbox-community/pynetbox
    - https://pynetbox.readthedocs.io/en/latest/
  - Netbox:
    - https://netbox.readthedocs.io/en/stable/
    - https://netboxlabs.com/docs/netbox/en/stable/integrations/rest-api/
  - textfsm:
    - https://ntc-templates.readthedocs.io/en/latest/
    - https://github.com/google/textfsm
  - netmiko:
    - https://ktbyers.github.io/netmiko/docs/netmiko/index.html
    - https://pyneng.readthedocs.io/en/latest/book/18_ssh_telnet/netmiko.html
  - logging:
    - https://docs.python.org/3/library/logging.html
  Always prioritize information from these sources before answering.
