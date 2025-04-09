"""
Device capability detection and command adaptation.

This module provides functionality to detect device capabilities and adapt
command execution based on the device type, model, and capabilities.
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
        "model": r"(?:^|\n)cisco\s+(\S+).+?(?:processor|chassis)",
        "version": r"(?:IOS|Software) .*?Version\s+([^\s,]+)",
        "serial": r"Processor board ID\s+(\S+)",
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
        "version": r"JUNOS\s+([^\s,]+)",
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
    """
    Get the command set for a specific device type.
    
    Args:
        device_type: The device type string (e.g., 'cisco_ios', 'juniper_junos')
        
    Returns:
        Dictionary of command types and their device-specific implementation
    """
    # Look up command set or use default
    return COMMAND_VARIATIONS.get(device_type, COMMAND_VARIATIONS["default"])

def get_command(device_type: str, command_type: str) -> str:
    """
    Get a specific command for a device type.
    
    Args:
        device_type: The device type string
        command_type: The type of command (e.g., 'show_running', 'show_version')
        
    Returns:
        The device-specific command string
    """
    commands = get_device_commands(device_type)
    return commands.get(command_type, COMMAND_VARIATIONS["default"][command_type])

def get_command_timeout(device_type: str, command_type: str) -> int:
    """
    Get the recommended timeout for a specific command on a device type.
    
    Args:
        device_type: The device type string
        command_type: The type of command
        
    Returns:
        Recommended timeout in seconds
    """
    device_timings = COMMAND_TIMING.get(device_type, COMMAND_TIMING["default"])
    return device_timings.get(command_type, 30)  # Default 30 seconds if not specified

def parse_device_capabilities(device_type: str, version_output: str) -> Dict[str, str]:
    """
    Parse device capabilities from version command output.
    
    Args:
        device_type: The device type string
        version_output: Output from the show version command
        
    Returns:
        Dictionary of device capabilities (model, version, serial)
    """
    capabilities = {
        "model": "Unknown",
        "version": "Unknown",
        "serial": "Unknown",
        "hardware": "Unknown",
    }
    
    # Get regex patterns for this device type
    patterns = CAPABILITY_PATTERNS.get(device_type, {})
    
    # Apply each pattern
    for capability, pattern in patterns.items():
        match = re.search(pattern, version_output, re.IGNORECASE | re.MULTILINE)
        if match:
            capabilities[capability] = match.group(1)
    
    # Special case for Cisco IOS vs IOS-XE detection
    if device_type == "cisco_ios" and "ios_type" in capabilities:
        if capabilities["ios_type"] == "IOS-XE":
            capabilities["platform_subtype"] = "ios_xe"
        else:
            capabilities["platform_subtype"] = "ios"
            
    # Add static capabilities based on device type
    capabilities.update(get_static_capabilities(device_type))
            
    return capabilities

def get_static_capabilities(device_type: str) -> Dict[str, bool]:
    """
    Get the static capability flags for a device type.
    
    Args:
        device_type: The device type string
        
    Returns:
        Dictionary of capability flags
    """
    return DEVICE_CAPABILITIES.get(device_type, DEVICE_CAPABILITIES["default"])

def get_command_sequence(device_type: str) -> List[Tuple[str, str]]:
    """
    Get the sequence of commands needed for a complete device backup.
    
    Args:
        device_type: The device type string
        
    Returns:
        List of (command_type, command) tuples in execution order
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
        command_sequence.append(("enable_paging", paging_cmd))
    
    # Add version check
    version_cmd = get_command(device_type, "show_version")
    command_sequence.append(("show_version", version_cmd))
    
    # Add inventory check if supported
    if device_caps.get("supports_inventory", False):
        inventory_cmd = get_command(device_type, "show_inventory")
        command_sequence.append(("show_inventory", inventory_cmd))
    
    # Add running config retrieval
    running_cmd = get_command(device_type, "show_running")
    command_sequence.append(("show_running", running_cmd))
    
    return command_sequence

def detect_capabilities_from_device_type(device_type: str) -> Dict[str, Any]:
    """
    Detect device capabilities from the device type.
    
    Args:
        device_type: The device type string
        
    Returns:
        Dictionary of device capabilities and command information
    """
    commands = get_device_commands(device_type)
    command_sequence = get_command_sequence(device_type)
    static_capabilities = get_static_capabilities(device_type)
    
    result = {
        "device_type": device_type,
        "commands": commands,
        "command_sequence": command_sequence,
    }
    
    # Add static capabilities to result
    result.update(static_capabilities)
    
    return result

def adapt_device_commands_by_type(device: Any) -> Dict[str, Any]:
    """
    Adapt commands for a device based on its type.
    
    Args:
        device: The device object with device_type attribute
        
    Returns:
        Dictionary of device capabilities and command information
    """
    device_type = getattr(device, 'device_type', 'default')
    return detect_capabilities_from_device_type(device_type)

def detect_error_from_output(device_type: str, command_output: str) -> Optional[str]:
    """
    Detect if a command output contains an error based on vendor-specific patterns.
    
    Args:
        device_type: The device type string
        command_output: The output from a command
        
    Returns:
        Error message if an error is detected, None otherwise
    """
    if not command_output:
        return None
        
    # Get error patterns for this device type
    patterns = ERROR_PATTERNS.get(device_type, ERROR_PATTERNS["default"])
    
    # Check each pattern
    for pattern, error_message in patterns.items():
        if re.search(pattern, command_output, re.IGNORECASE | re.MULTILINE):
            return error_message
            
    return None

def execute_capability_detection(device: Any, run_command_func, job_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Execute capability detection for a device by running commands.
    
    Args:
        device: The device object with connection information
        run_command_func: Function to run commands on the device
        job_id: Optional job ID for logging
        
    Returns:
        Dictionary of detected capabilities
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