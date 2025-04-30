"""
Device capability detection and command adaptation.

This module provides functionality to detect device capabilities and adapt
command execution based on the device type, model, and capabilities.

It includes patterns to automatically detect device information from command outputs,
mappings for device-specific commands, timeout settings, and functions to dynamically
adapt operations based on detected capabilities.

Key components include:
- Command mapping for different device types
- Timeout settings customized by device type and command
- Pattern-based capability detection from device outputs
- Device capability flags for feature support
- Functions to adapt commands based on detected capabilities

The module is central to the system's ability to work with diverse network devices,
providing a layer of abstraction that allows the core logic to operate consistently
across different vendor implementations and device models.
"""

import re
from typing import Dict, Any, Optional, List, Tuple, Callable
from netraven.utils.unified_logger import get_unified_logger

logger = get_unified_logger()

# Mapping of device types to command variations
COMMAND_VARIATIONS = {
    # Cisco IOS/IOS-XE
    "cisco_ios": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "write memory",
        "enable_paging": "terminal length 0",
        "show_inventory": "show inventory",
        "enter_enable": "enable",
    },
    
    # Cisco IOS-XR
    "cisco_xr": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "commit",
        "enable_paging": "terminal length 0",
        "show_inventory": "show inventory",
        "enter_enable": "", # Already in privileged mode by default
    },
    
    # Cisco NX-OS
    "cisco_nxos": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "copy running-config startup-config",
        "enable_paging": "terminal length 0",
        "show_inventory": "show inventory",
        "enter_enable": "", # Already in privileged mode by default
    },
    
    # Arista EOS
    "arista_eos": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "write memory",
        "enable_paging": "terminal length 0",
        "show_inventory": "show inventory",
        "enter_enable": "", # Already in privileged mode by default
    },
    
    # Juniper Junos
    "juniper_junos": {
        "show_running": "show configuration | display set",
        "show_version": "show version",
        "save_config": "commit",
        "enable_paging": "set cli screen-length 0",
        "show_inventory": "show chassis hardware",
        "enter_cli": "cli",
    },
    
    # Cisco ASA
    "cisco_asa": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "write memory",
        "enable_paging": "terminal pager 0",
        "show_inventory": "show inventory",
        "enter_enable": "enable",
    },
    
    # Palo Alto PAN-OS
    "paloalto_panos": {
        "show_running": "show config running",
        "show_version": "show system info",
        "save_config": "commit",
        "enable_paging": "set cli pager off",
        "show_inventory": "show system info",
        "enter_cli": "set cli config-output-format set",
    },
    
    # F5 BIG-IP
    "f5_tmsh": {
        "show_running": "show running-config",
        "show_version": "show sys version",
        "save_config": "save sys config",
        "enable_paging": "modify cli preference pager disabled",
        "show_inventory": "show sys hardware",
        "enter_cli": "tmsh",
    },
    
    # Default fallback
    "default": {
        "show_running": "show running-config",
        "show_version": "show version",
        "save_config": "write memory",
        "enable_paging": "terminal length 0",
        "show_inventory": "show inventory",
        "enter_enable": "enable",
    },
}

# Command timing requirements (in seconds)
COMMAND_TIMING = {
    "cisco_ios": {
        "show_running": 60,  # May take longer for larger configs
        "show_version": 10,
        "enable_paging": 5,
    },
    "juniper_junos": {
        "show_running": 90,  # Juniper configs can be large and take longer
        "show_version": 10,
        "enable_paging": 5,
    },
    "f5_tmsh": {
        "show_running": 120,  # F5 configs are typically very large
        "show_version": 10,
        "enable_paging": 5,
    },
    "paloalto_panos": {
        "show_running": 90,
        "show_version": 15,
        "enable_paging": 5,
    },
    "default": {
        "show_running": 60,
        "show_version": 10,
        "enable_paging": 5,
    }
}

# Improved regex patterns for parsing device capabilities from version output
CAPABILITY_PATTERNS = {
    "cisco_ios": {
        "model": r"cisco\s+(\S+(?:-\S+)?)\s+(?:\(|processor)",
        "version": r"(?:IOS|Software) .*?Version\s+([^\s,]+)",
        "serial": r"[Pp]rocessor board ID\s+(\S+)",
        "ios_type": r"(IOS-XE|IOS)",  # Detect IOS vs IOS-XE
    },
    "cisco_xr": {
        "model": r"(?:^|\n)cisco\s+(\S+).+?processor",
        "version": r"IOS XR Software.*?Version\s+([^\s,]+)",
        "serial": r"Processor board ID\s+(\S+)",
    },
    "cisco_nxos": {
        "model": r"cisco\s+Nexus\s+(\S+)",
        "version": r"NXOS: version\s+([^\s,]+)",
        "serial": r"Processor Board ID\s+(\S+)",
    },
    "arista_eos": {
        "model": r"(?:^|\n)Arista\s+(\S+)",
        "version": r"EOS version:\s+(\S+)",
        "serial": r"Serial number:\s+(\S+)",
        "hardware": r"Hardware version:\s+(\S+)",
    },
    "juniper_junos": {
        "model": r"Model:\s+(\S+)",
        "version": r"JUNOS.*?\[([^\[\]]+)\]",
        "serial": r"Chassis\s+(\S+)",
        "hardware": r"Hardware model:\s+(\S+)",
    },
    "cisco_asa": {
        "model": r"Hardware:\s+(\S+),",
        "version": r"ASA.*?Version\s+([^\s,]+)",
        "serial": r"Serial Number:\s+(\S+)",
    },
    "paloalto_panos": {
        "model": r"model:\s+(\S+)",
        "version": r"sw-version:\s+(\S+)",
        "serial": r"serial:\s+(\S+)",
        "hardware": r"hw-version:\s+(\S+)",
    },
    "f5_tmsh": {
        "model": r"Platform\s+Name\s+(\S+)",
        "version": r"Version\s+([^\s,]+)",
        "serial": r"Appliance\s+Serial\s+(\S+)",
        "hardware": r"Platform\s+Id\s+(\S+)",
    },
}

# Device capability flags
DEVICE_CAPABILITIES = {
    "cisco_ios": {
        "requires_enable": True,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": False,
        "supports_file_transfer": True,
    },
    "cisco_xr": {
        "requires_enable": False,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": True,
        "supports_file_transfer": True,
    },
    "cisco_nxos": {
        "requires_enable": False,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": True,
        "supports_file_transfer": True,
    },
    "arista_eos": {
        "requires_enable": False,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": True,
        "supports_file_transfer": True,
    },
    "juniper_junos": {
        "requires_enable": False,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": True,
        "supports_file_transfer": True,
        "requires_cli_mode": True,
    },
    "cisco_asa": {
        "requires_enable": True,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": False,
        "supports_file_transfer": False,
    },
    "paloalto_panos": {
        "requires_enable": False,
        "supports_paging_control": True, 
        "supports_inventory": False,
        "supports_config_replace": False,
        "supports_file_transfer": False,
        "requires_cli_mode": True,
    },
    "f5_tmsh": {
        "requires_enable": False,
        "supports_paging_control": True,
        "supports_inventory": True,
        "supports_config_replace": False,
        "supports_file_transfer": False,
        "requires_cli_mode": True,
    },
    "default": {
        "requires_enable": True,
        "supports_paging_control": True,
        "supports_inventory": False,
        "supports_config_replace": False,
        "supports_file_transfer": False,
    }
}

# Vendor-specific error patterns and their meanings
ERROR_PATTERNS = {
    "cisco_ios": {
        r"% Invalid input detected": "Invalid command syntax",
        r"% Incomplete command": "Command is incomplete",
        r"% Ambiguous command": "Command is ambiguous",
        r"% Authorization failed": "Authorization failed for command",
    },
    "juniper_junos": {
        r"unknown command": "Invalid command syntax",
        r"syntax error": "Command syntax error",
        r"permission denied": "Authorization failed for command",
    },
    "paloalto_panos": {
        r"Invalid syntax": "Command syntax error",
        r"Unknown command": "Invalid command",
        r"Permission denied": "Authorization failed for command",
    },
    "default": {
        r"error|invalid|failed|denied": "Command error",
    }
}

def get_device_commands(device_type: str) -> Dict[str, str]:
    """Get all command variations for a specific device type.
    
    Retrieves the complete dictionary of standard command mappings for 
    a given device type, providing access to all the command variations
    available for that specific platform.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
    
    Returns:
        Dict[str, str]: Dictionary mapping command types to device-specific commands
                       for the requested device type, or default commands if the
                       device type is not recognized
    
    Example:
        >>> commands = get_device_commands("cisco_ios")
        >>> commands["show_running"]
        'show running-config'
    """
    if device_type in COMMAND_VARIATIONS:
        return COMMAND_VARIATIONS[device_type]
    else:
        logger.log(f"Unknown device type: {device_type}, using default commands", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities")
        return COMMAND_VARIATIONS["default"]

def get_command(device_type: str, command_type: str) -> str:
    """Get the device-specific command for a standard command type.
    
    Translates a generic command type (like "show_running") to the
    device-specific implementation of that command. This allows code to
    use standard command types that work across all device types without
    needing to know the specific syntax for each platform.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
        command_type (str): The generic command type (e.g., "show_running", "save_config")
    
    Returns:
        str: The device-specific command string for the requested command type,
            or the default command if either the device type or command type
            is not recognized
    
    Example:
        >>> get_command("juniper_junos", "show_running")
        'show configuration | display set'
        >>> get_command("cisco_ios", "save_config")
        'write memory'
    """
    commands = get_device_commands(device_type)
    
    if command_type in commands:
        return commands[command_type]
    else:
        logger.log(f"Unknown command type: {command_type} for device: {device_type}", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities")
        # See if it exists in the default commands
        if command_type in COMMAND_VARIATIONS["default"]:
            return COMMAND_VARIATIONS["default"][command_type]
        else:
            # Last resort, just return the command type as-is
            logger.log(f"No default found for command type: {command_type}", level="ERROR", destinations=["stdout", "file", "db"], source="device_capabilities")
            return command_type

def get_command_timeout(device_type: str, command_type: str) -> int:
    """Get the recommended timeout for a specific command on a device type.
    
    Different device types and commands require different timeout values.
    This function returns the recommended timeout in seconds for a specific
    combination of device type and command type.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
        command_type (str): The generic command type (e.g., "show_running", "show_version")
    
    Returns:
        int: The recommended timeout in seconds for the requested command
            on the specified device type. Falls back to default timeouts
            if specific values are not defined.
    
    Example:
        >>> get_command_timeout("f5_tmsh", "show_running")
        120  # F5 configs can be large, need longer timeout
        >>> get_command_timeout("cisco_ios", "show_version")
        10  # Version command is typically quick to return
    """
    # Default timeout if nothing else is defined
    default_timeout = 30
    
    # Check if we have specific timing for this device type
    if device_type in COMMAND_TIMING:
        device_timing = COMMAND_TIMING[device_type]
        if command_type in device_timing:
            return device_timing[command_type]
    
    # Fall back to default device type timing
    if command_type in COMMAND_TIMING["default"]:
        return COMMAND_TIMING["default"][command_type]
    
    # Last resort
    logger.log(
        f"No timeout defined for {device_type}/{command_type}, "
        f"using default: {default_timeout}s",
        level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities"
    )
    return default_timeout

def parse_device_capabilities(device_type: str, version_output: str) -> Dict[str, str]:
    """Extract device capabilities from command output using regex patterns.
    
    Parses the output of "show version" or similar commands to extract
    device metadata like model, version, serial number, etc. using
    device-specific regex patterns.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
        version_output (str): The output text from the version command
    
    Returns:
        Dict[str, str]: Dictionary of capabilities with keys like:
                       - model: Device model/platform
                       - version: OS/firmware version
                       - serial: Serial number
                       - hardware: Hardware version/model (if available)
                       - Other device-specific capabilities
    
    Example:
        >>> version_output = "cisco WS-C3750X-48P processor with 262144K bytes of memory"
        >>> parse_device_capabilities("cisco_ios", version_output)
        {'model': 'WS-C3750X-48P', ...}
    
    Note:
        The function gracefully handles missing patterns by returning
        empty strings for capabilities that couldn't be extracted.
    """
    result = {}
    
    # Get the regex patterns for this device type, or use default
    if device_type in CAPABILITY_PATTERNS:
        patterns = CAPABILITY_PATTERNS[device_type]
    else:
        logger.log(f"No capability patterns defined for {device_type}, using limited detection", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities")
        patterns = {}
    
    # Apply each pattern and extract capabilities
    for capability, pattern in patterns.items():
        match = re.search(pattern, version_output, re.IGNORECASE | re.MULTILINE)
        if match:
            result[capability] = match.group(1)
        else:
            result[capability] = ""
            logger.log(f"[Job: {job_id}] Could not parse {capability} from output for {device_name}", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities", job_id=job_id)
    
    return result

def get_static_capabilities(device_type: str) -> Dict[str, bool]:
    """Get the static capability flags for a device type.
    
    Returns the predefined capability flags for a device type,
    indicating what features the device supports, such as whether
    it requires enable mode, supports paging control, etc.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
    
    Returns:
        Dict[str, bool]: Dictionary of capability flags with keys like:
                        - requires_enable: Whether enable mode is needed
                        - supports_paging_control: Whether paging can be disabled
                        - supports_inventory: Whether inventory commands exist
                        - supports_config_replace: Whether config can be replaced
                        - supports_file_transfer: Whether file transfers are supported
                        - requires_cli_mode: Whether CLI mode must be entered
    
    Example:
        >>> get_static_capabilities("cisco_ios")
        {'requires_enable': True, 'supports_paging_control': True, ...}
    """
    if device_type in DEVICE_CAPABILITIES:
        return DEVICE_CAPABILITIES[device_type]
    else:
        logger.log(f"No capability flags defined for {device_type}, using defaults", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities")
        return DEVICE_CAPABILITIES["default"]

def get_command_sequence(device_type: str) -> List[Tuple[str, str]]:
    """Get the recommended command sequence for connecting to a device.
    
    Returns an ordered list of commands that should be executed when
    connecting to a device, based on its type. The sequence includes
    commands for entering the right mode, disabling paging, etc.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
    
    Returns:
        List[Tuple[str, str]]: List of tuples where each tuple contains:
                              - Command purpose/type (string)
                              - Actual command to execute (string)
                              
    Example:
        >>> get_command_sequence("cisco_ios")
        [('enter_enable', 'enable'), ('enable_paging', 'terminal length 0')]
        >>> get_command_sequence("juniper_junos")
        [('enter_cli', 'cli'), ('enable_paging', 'set cli screen-length 0')]
    """
    sequence = []
    capabilities = get_static_capabilities(device_type)
    
    # Add enable command if required
    if capabilities.get("requires_enable", False):
        enable_cmd = get_command(device_type, "enter_enable")
        if enable_cmd:  # Only add if not empty
            sequence.append(("enter_enable", enable_cmd))
    
    # Add CLI mode entry if required
    if capabilities.get("requires_cli_mode", False):
        cli_cmd = get_command(device_type, "enter_cli")
        if cli_cmd:  # Only add if not empty
            sequence.append(("enter_cli", cli_cmd))
    
    # Add paging control if supported
    if capabilities.get("supports_paging_control", True):
        paging_cmd = get_command(device_type, "enable_paging")
        sequence.append(("enable_paging", paging_cmd))
    
    return sequence

def detect_capabilities_from_device_type(device_type: str) -> Dict[str, Any]:
    """Generate baseline capabilities based solely on device type.
    
    This function creates a capabilities dictionary using only the device type,
    without requiring any device connection. It's useful for initial setup
    before connecting to a device or when device access isn't available.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
    
    Returns:
        Dict[str, Any]: Combined capability dictionary with:
                       - Static capability flags (requires_enable, etc.)
                       - Command variations for this device type
                       - Command sequence for connection
                       - No dynamic capabilities (model, version, etc.)
    
    Example:
        >>> capabilities = detect_capabilities_from_device_type("cisco_ios")
        >>> capabilities["requires_enable"]
        True
        >>> capabilities["commands"]["show_running"]
        'show running-config'
    """
    capabilities = {}
    
    # Get static capabilities
    static_capabilities = get_static_capabilities(device_type)
    capabilities.update(static_capabilities)
    
    # Add command dictionary
    capabilities["commands"] = get_device_commands(device_type)
    
    # Add command sequence
    capabilities["connection_sequence"] = get_command_sequence(device_type)
    
    # Add device type for reference
    capabilities["device_type"] = device_type
    
    # Initialize placeholders for dynamic capabilities
    capabilities["model"] = "Unknown"
    capabilities["version"] = "Unknown"
    capabilities["serial"] = "Unknown"
    capabilities["hardware"] = "Unknown"
    
    return capabilities

def adapt_device_commands_by_type(device: Any) -> Dict[str, Any]:
    """Adapt commands for a specific device based on its type.
    
    This is a convenience function that takes a device object,
    extracts its device_type attribute, and returns a capabilities
    dictionary for that device type.
    
    Args:
        device (Any): A device object with a device_type attribute
    
    Returns:
        Dict[str, Any]: Capabilities dictionary for the device type
                       (Same as detect_capabilities_from_device_type)
    
    Raises:
        AttributeError: If the device object doesn't have a device_type attribute
    """
    device_type = getattr(device, "device_type", "default")
    return detect_capabilities_from_device_type(device_type)

def detect_error_from_output(device_type: str, command_output: str) -> Optional[str]:
    """Detect error messages in command output based on device type.
    
    Analyzes command output for device-specific error patterns to determine
    if a command failed, even if no exception was raised. This is useful for
    detecting permission errors, syntax errors, etc. that some devices
    return as normal output instead of raising exceptions.
    
    Args:
        device_type (str): The Netmiko device type (e.g., "cisco_ios", "juniper_junos")
        command_output (str): The output text from a command
    
    Returns:
        Optional[str]: Error message if an error was detected, or None if
                      the output appears normal
    
    Example:
        >>> output = "% Invalid input detected at '^' marker."
        >>> detect_error_from_output("cisco_ios", output)
        'Command syntax error detected: Invalid input detected'
    """
    # Common error patterns by device type
    error_patterns = {
        "cisco_ios": [
            (r"%\s+Invalid input detected", "Command syntax error detected: Invalid input detected"),
            (r"%\s+Incomplete command", "Command syntax error: Incomplete command"),
            (r"% Authorization failed", "Authorization error: Insufficient privileges"),
        ],
        "juniper_junos": [
            (r"error:\s+(.*)", "Juniper configuration error: {}"),
            (r"unknown command", "Command syntax error: Unknown command"),
        ],
        "cisco_nxos": [
            (r"% Invalid command", "Command syntax error: Invalid command"),
            (r"% Permission denied", "Authorization error: Permission denied"),
        ],
        "default": [
            (r"(?:error|invalid|failed)", "Command error detected in output"),
        ]
    }
    
    # Get patterns for this device type or use default
    patterns = error_patterns.get(device_type, error_patterns["default"])
    
    # Check each pattern
    for pattern, message_template in patterns:
        match = re.search(pattern, command_output, re.IGNORECASE)
        if match:
            # If the pattern has a capture group, format the message with it
            if len(match.groups()) > 0:
                return message_template.format(match.group(1))
            else:
                return message_template
    
    # No error detected
    return None

def execute_capability_detection(
    device: Any, 
    run_command_func: Callable, 
    job_id: Optional[int] = None
) -> Dict[str, Any]:
    """Execute comprehensive device capability detection.
    
    This function performs full device capability detection by:
    1. Getting static capabilities based on device type
    2. Connecting to the device and running "show version" or equivalent
    3. Parsing the version output for dynamic capabilities
    
    This gives a complete picture of the device's capabilities and metadata,
    which can be used to adapt command execution, tailor timeouts, etc.
    
    Args:
        device (Any): Device object with required connection attributes
        run_command_func (Callable): Function to run commands on the device,
                                   with signature run_command(device, job_id, command, config)
        job_id (Optional[int]): Job ID for correlation and logging
    
    Returns:
        Dict[str, Any]: Complete capabilities dictionary with:
                       - Static capability flags (requires_enable, etc.)
                       - Dynamic properties (model, version, serial, etc.)
                       - Command variations for this device type
                       - Command sequence for connection
    
    Example:
        >>> capabilities = execute_capability_detection(device, run_command)
        >>> print(f"Device model: {capabilities['model']}, version: {capabilities['version']}")
        Device model: WS-C3750X-48P, version: 15.2(4)E5
    
    Note:
        This function handles errors during capability detection gracefully,
        falling back to static capabilities if dynamic detection fails.
    """
    # Get device type
    device_type = getattr(device, "device_type", "default")
    device_id = getattr(device, "id", 0)
    device_name = getattr(device, "hostname", f"Device_{device_id}")
    
    # Start with static capabilities
    capabilities = detect_capabilities_from_device_type(device_type)
    
    # Try to get dynamic capabilities
    try:
        # Get the version command for this device type
        version_cmd = get_command(device_type, "show_version")
        
        # Run the command
        logger.log(f"[Job: {job_id}] Detecting capabilities for {device_name} using '{version_cmd}'", level="INFO", destinations=["stdout", "file", "db"], source="device_capabilities", job_id=job_id)
        version_output = run_command_func(device, job_id, command=version_cmd)
        
        if version_output:
            # Parse the output for capabilities
            dynamic_caps = parse_device_capabilities(device_type, version_output)
            
            # Update capabilities with dynamic information
            capabilities.update(dynamic_caps)
            
            logger.log(
                f"[Job: {job_id}] Capability detection result for {device_name}: {capabilities}",
                level="INFO", destinations=["stdout", "file"], source="device_capabilities", job_id=job_id
            )
        else:
            logger.log(f"[Job: {job_id}] Empty output from version command for {device_name}", level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities", job_id=job_id)
            
    except Exception as e:
        logger.log(
            f"[Job: {job_id}] Capability detection failed for {device_name}: {e}",
            level="WARNING", destinations=["stdout", "file", "db"], source="device_capabilities", job_id=job_id
        )
        # Continue with static capabilities only
    
    return capabilities 