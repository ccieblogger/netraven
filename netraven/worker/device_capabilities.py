"""
Device capability detection and command adaptation.

This module provides functionality to detect device capabilities and adapt
command execution based on the device type, model, and capabilities.

It includes patterns to automatically detect device information from command outputs,
mappings for device-specific commands, timeout settings, and functions to dynamically
adapt operations based on detected capabilities.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

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
    """Get all available commands for a specific device type.
    
    Retrieves the full mapping of command types to actual command strings for the 
    specified device type. Falls back to default commands if the device type is not recognized.
    
    Args:
        device_type: The type of device to get commands for (e.g., "cisco_ios")
        
    Returns:
        A dictionary mapping command types to actual command strings
    """
    if device_type in COMMAND_VARIATIONS:
        return COMMAND_VARIATIONS[device_type]
    return COMMAND_VARIATIONS["default"]

def get_command(device_type: str, command_type: str) -> str:
    """Get a specific command for a device type.
    
    Retrieves the actual command string for a given command type on the specified device type.
    Falls back to the default command if either the device type or command type is not recognized.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        command_type: The type of command to retrieve (e.g., "show_running")
        
    Returns:
        The actual command string to execute on the device
    """
    commands = get_device_commands(device_type)
    if command_type in commands:
        return commands[command_type]
    
    # Fall back to default if this command type isn't defined for this device
    if command_type in COMMAND_VARIATIONS["default"]:
        return COMMAND_VARIATIONS["default"][command_type]
    
    # Return empty string if command not found
    return ""

def get_command_timeout(device_type: str, command_type: str) -> int:
    """Get the appropriate timeout value for a command on a device type.
    
    Different commands may require different timeout values depending on the device type.
    This function retrieves the timeout value in seconds for the specified command and device.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        command_type: The type of command to get timeout for (e.g., "show_running")
        
    Returns:
        The timeout value in seconds for the command
    """
    # First look for device-specific timeout
    if device_type in COMMAND_TIMING and command_type in COMMAND_TIMING[device_type]:
        return COMMAND_TIMING[device_type][command_type]
    
    # Then try default timeout for this command type
    if command_type in COMMAND_TIMING["default"]:
        return COMMAND_TIMING["default"][command_type]
    
    # Fallback default
    return 30  # Default timeout of 30 seconds

def parse_device_capabilities(device_type: str, version_output: str) -> Dict[str, str]:
    """Parse device capabilities from version output.
    
    Extracts device model, version, serial number, and other capabilities from the output
    of a version command by applying device-specific regex patterns.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        version_output: The output from the show version command or equivalent
        
    Returns:
        A dictionary containing extracted capability information (model, version, serial, etc.)
    """
    capabilities = {}
    
    # Use default patterns if device type not recognized
    patterns = CAPABILITY_PATTERNS.get(device_type, CAPABILITY_PATTERNS.get("cisco_ios", {}))
    
    # Apply each pattern and extract the information
    for capability, pattern in patterns.items():
        match = re.search(pattern, version_output, re.MULTILINE | re.DOTALL)
        if match:
            capabilities[capability] = match.group(1).strip()
    
    return capabilities

def get_static_capabilities(device_type: str) -> Dict[str, bool]:
    """Get static (non-detectable) capabilities for a device type.
    
    Returns information about device capabilities that are known based on the device type,
    rather than being detected from command output.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        
    Returns:
        A dictionary mapping capability names to boolean values
    """
    if device_type in DEVICE_CAPABILITIES:
        return DEVICE_CAPABILITIES[device_type]
    return DEVICE_CAPABILITIES.get("default", {})

def get_command_sequence(device_type: str) -> List[Tuple[str, str]]:
    """Get the sequence of commands for a device type.
    
    Returns the ordered sequence of commands that should be executed
    when connecting to a device to properly initialize the session.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        
    Returns:
        A list of (command_type, actual_command) tuples in execution order
    """
    device_caps = get_static_capabilities(device_type)
    command_sequence = []
    
    # Add device-specific CLI mode entry if needed
    if device_caps.get("requires_cli_mode", False):
        cli_cmd = get_command(device_type, "enter_cli")
        if cli_cmd:
            command_sequence.append(("enter_cli", cli_cmd))
    
    # Add enable command if required
    if device_caps.get("requires_enable", False):
        enable_cmd = get_command(device_type, "enter_enable")
        if enable_cmd:
            command_sequence.append(("enter_enable", enable_cmd))
    
    # Add paging control
    if device_caps.get("supports_paging_control", True):
        paging_cmd = get_command(device_type, "enable_paging")
        if paging_cmd:
            command_sequence.append(("enable_paging", paging_cmd))
    
    # Add version check
    version_cmd = get_command(device_type, "show_version")
    if version_cmd:
        command_sequence.append(("show_version", version_cmd))
    
    # Add inventory check if supported
    if device_caps.get("supports_inventory", False):
        inventory_cmd = get_command(device_type, "show_inventory")
        if inventory_cmd:
            command_sequence.append(("show_inventory", inventory_cmd))
    
    # Add running config retrieval
    running_cmd = get_command(device_type, "show_running")
    if running_cmd:
        command_sequence.append(("show_running", running_cmd))
    
    return command_sequence

def detect_capabilities_from_device_type(device_type: str) -> Dict[str, Any]:
    """Detect capabilities from device type without device interaction.
    
    Creates a capabilities dictionary based solely on the device type,
    without executing any commands on the device.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        
    Returns:
        A dictionary containing basic capability information
    """
    # Start with empty capabilities
    capabilities = {}
    
    # Add static capabilities
    capabilities.update(get_static_capabilities(device_type))
    
    # Add command mappings
    capabilities["commands"] = get_device_commands(device_type)
    
    # Add empty placeholders for dynamic capabilities
    capabilities["model"] = "Unknown"
    capabilities["version"] = "Unknown"
    capabilities["serial"] = "Unknown"
    capabilities["hardware"] = "Unknown"
    
    return capabilities

def adapt_device_commands_by_type(device: Any) -> Dict[str, Any]:
    """Adapt commands for a device based on its type.
    
    Creates a dictionary of device-specific commands and capabilities
    based on the device object's device_type attribute.
    
    Args:
        device: Device object with a device_type attribute
        
    Returns:
        A dictionary containing device-specific command mappings and capabilities
    """
    device_type = getattr(device, "device_type", "default")
    return detect_capabilities_from_device_type(device_type)

def detect_error_from_output(device_type: str, command_output: str) -> Optional[str]:
    """Detect errors in command output based on device type.
    
    Analyzes command output for device-specific error patterns and returns
    an error message if an error is detected.
    
    Args:
        device_type: The type of device (e.g., "cisco_ios")
        command_output: The output from a command execution
        
    Returns:
        An error message if an error is detected, None otherwise
    """
    # Common error patterns
    error_patterns = {
        "cisco_ios": [
            r"% Invalid input",
            r"% Incomplete command",
            r"% Command rejected",
            r"% Error",
        ],
        "juniper_junos": [
            r"syntax error",
            r"unknown command",
            r"error:",
        ],
        "default": [
            r"% Invalid",
            r"% Error",
            r"syntax error",
            r"unknown command",
        ]
    }
    
    # Get device-specific patterns or fall back to default
    patterns = error_patterns.get(device_type, error_patterns["default"])
    
    # Check each pattern
    for pattern in patterns:
        if re.search(pattern, command_output, re.IGNORECASE):
            return f"Error detected in command output: {pattern}"
    
    return None

def execute_capability_detection(device: Any, run_command_func, job_id: Optional[int] = None) -> Dict[str, Any]:
    """Execute capability detection on a device.
    
    Connects to a device, executes commands to detect capabilities, and returns
    a comprehensive capabilities dictionary.
    
    This function is the main entry point for device capability detection.
    
    Args:
        device: Device object with connection attributes
        run_command_func: Function to execute commands on the device
        job_id: Optional job ID for logging
        
    Returns:
        A dictionary containing comprehensive capability information
    """
    device_type = getattr(device, 'device_type', 'default')
    device_caps = detect_capabilities_from_device_type(device_type)
    detected_capabilities = {}
    
    try:
        # Try to get version information
        version_cmd = get_command(device_type, "show_version")
        version_output = run_command_func(device, job_id, command=version_cmd)
        
        # Parse capabilities from version output
        if version_output:
            detected_capabilities = parse_device_capabilities(device_type, version_output)
            detected_capabilities["version_command_output"] = version_output
            
        # Try to get inventory if supported
        if device_caps.get("supports_inventory", False):
            inventory_cmd = get_command(device_type, "show_inventory")
            inventory_output = run_command_func(device, job_id, command=inventory_cmd)
            if inventory_output:
                detected_capabilities["inventory_output"] = inventory_output
                
        # Add static capabilities
        detected_capabilities.update(device_caps)
        
    except Exception as e:
        logger.error(f"Error during capability detection for device type {device_type}: {str(e)}")
        # Return just the static capabilities if dynamic detection fails
        detected_capabilities = device_caps
        
    return detected_capabilities 