"""
Mock Device Connector for testing network device interactions.

This module provides mock classes for simulating network device connections
and responses for testing without actual network connectivity.
"""

import time
import random
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import MagicMock

class MockDeviceConnector:
    """
    Mock device connector that simulates connections to network devices.
    
    This class mimics the behavior of the DeviceConnector class but doesn't
    require actual network connectivity. It can be configured to simulate
    success and failure scenarios.
    """
    
    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None,
        failure_mode: str = "none",  # none, timeout, auth, unreachable, intermittent
        failure_count: int = 0,      # Number of failures before success
        response_delay: float = 0.0  # Simulated response delay in seconds
    ):
        """
        Initialize the MockDeviceConnector.
        
        Args:
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type
            port: SSH port number
            use_keys: Whether to use SSH key authentication
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds
            alt_passwords: List of alternative passwords to try
            failure_mode: Type of failure to simulate
            failure_count: Number of failures before success
            response_delay: Simulated response delay in seconds
        """
        self.host = host
        self.username = username
        self.password = password
        self.device_type = device_type or "cisco_ios"
        self.port = port
        self.use_keys = use_keys
        self.key_file = key_file
        self.timeout = timeout
        self.alt_passwords = alt_passwords or []
        
        # Mock configuration
        self.failure_mode = failure_mode
        self.failure_count = failure_count
        self.response_delay = response_delay
        self.attempt_count = 0
        
        # Connection state
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        return self._connected
    
    def connect(self) -> bool:
        """
        Simulate connecting to the device.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Increment attempt counter
        self.attempt_count += 1
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Handle failure modes
        if self.failure_mode != "none":
            # Intermittent failures
            if self.failure_mode == "intermittent":
                # Fail randomly with 50% chance
                if random.random() < 0.5 and self.attempt_count <= self.failure_count:
                    return False
            # Fixed number of failures then success
            elif self.attempt_count <= self.failure_count:
                return False
        
        # If we didn't fail, succeed
        self._connected = True
        return True
    
    def disconnect(self) -> bool:
        """
        Simulate disconnecting from the device.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.is_connected:
            self._connected = False
            return True
        return False
    
    def get_running(self) -> Optional[str]:
        """
        Simulate retrieving the running configuration.
        
        Returns:
            Optional[str]: Mock running configuration as text, or None if retrieval failed
        """
        if not self.is_connected:
            return None
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Return mock configuration
        return f"""Building configuration...
Current configuration : 1278 bytes
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname {self.host}
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
!
ip routing
!
end"""
    
    def get_serial(self) -> Optional[str]:
        """
        Simulate retrieving the device serial number.
        
        Returns:
            Optional[str]: Mock serial number, or None if retrieval failed
        """
        if not self.is_connected:
            return None
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Generate deterministic "serial number" based on host
        host_hash = sum(ord(c) for c in self.host) % 10000
        return f"FTX{host_hash:04d}"
    
    def get_os(self) -> Optional[Dict[str, str]]:
        """
        Simulate retrieving the device operating system information.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary containing mock OS type and version,
                                     or None if retrieval failed
        """
        if not self.is_connected:
            return None
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Return mock OS info
        return {
            "type": "IOS-XE",
            "version": "16.12.3",
            "model": "C3850-48T"
        }
    
    def send_command(self, command: str) -> Optional[str]:
        """
        Simulate sending a command to the device.
        
        Args:
            command: Command to send
            
        Returns:
            Optional[str]: Mock command response, or None if failed
        """
        if not self.is_connected:
            return None
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Return mock response based on command
        if "show run" in command:
            return self.get_running()
        elif "show version" in command:
            return f"Cisco IOS Software, Version 16.12.3\nProcessor board ID {self.get_serial()}"
        elif "show interfaces" in command:
            return "GigabitEthernet0/0 is up, line protocol is up\n  Hardware is Gigabit Ethernet, address is aabb.cc00.1000"
        else:
            return f"Command response for: {command}"
    
    def __enter__(self):
        """Support for context manager interface."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure proper cleanup when used as context manager."""
        self.disconnect()


class MockJobDeviceConnector(MockDeviceConnector):
    """
    Mock JobDeviceConnector that extends MockDeviceConnector with job-specific features.
    
    This class mimics the behavior of the JobDeviceConnector class for testing
    job execution without actual device interaction.
    """
    
    def __init__(
        self,
        device_id: str,
        host: str,
        username: str,
        password: Optional[str] = None,
        device_type: Optional[str] = None,
        port: int = 22,
        use_keys: bool = False,
        key_file: Optional[str] = None,
        timeout: int = 30,
        alt_passwords: Optional[List[str]] = None,
        session_id: Optional[str] = "mock-session-id",
        user_id: Optional[str] = None,
        max_retries: int = 3,
        failure_mode: str = "none",
        failure_count: int = 0,
        response_delay: float = 0.0
    ):
        """
        Initialize the MockJobDeviceConnector.
        
        Args:
            device_id: Unique identifier for the device
            host: Device hostname or IP address
            username: Username for authentication
            password: Password for authentication
            device_type: Device type
            port: SSH port number
            use_keys: Whether to use SSH key authentication
            key_file: Path to SSH private key file
            timeout: Connection timeout in seconds
            alt_passwords: List of alternative passwords to try
            session_id: Session ID for logging
            user_id: User ID for database logging
            max_retries: Maximum number of connection attempts
            failure_mode: Type of failure to simulate
            failure_count: Number of failures before success
            response_delay: Simulated response delay in seconds
        """
        super().__init__(
            host=host,
            username=username,
            password=password,
            device_type=device_type,
            port=port,
            use_keys=use_keys,
            key_file=key_file,
            timeout=timeout,
            alt_passwords=alt_passwords,
            failure_mode=failure_mode,
            failure_count=failure_count,
            response_delay=response_delay
        )
        
        self.device_id = device_id
        self.session_id = session_id
        self.user_id = user_id
        self.max_retries = max_retries
        
        # Mock logging functions
        self.log_calls = {
            "connect": [],
            "connect_success": [],
            "connect_failure": [],
            "disconnect": [],
            "command": [],
            "response": []
        }
    
    def connect(self) -> bool:
        """
        Simulate connecting to the device with retry logic.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Log connection attempt
        self.log_calls["connect"].append({"device_id": self.device_id, "session_id": self.session_id})
        
        for attempt in range(1, self.max_retries + 1):
            # Increment attempt counter
            self.attempt_count += 1
            
            # Simulate response delay
            if self.response_delay > 0:
                time.sleep(self.response_delay)
            
            # Handle failure modes
            should_fail = False
            if self.failure_mode != "none":
                # Intermittent failures
                if self.failure_mode == "intermittent":
                    # Fail randomly with 50% chance
                    if random.random() < 0.5 and self.attempt_count <= self.failure_count:
                        should_fail = True
                # Fixed number of failures then success
                elif self.attempt_count <= self.failure_count:
                    should_fail = True
            
            if should_fail:
                error_msg = f"Connection failed (attempt {attempt}/{self.max_retries})"
                self.log_calls["connect_failure"].append({
                    "device_id": self.device_id, 
                    "session_id": self.session_id,
                    "error": error_msg
                })
                
                # If this was the last attempt, return failure
                if attempt == self.max_retries:
                    return False
                
                # Otherwise wait before retrying
                backoff_seconds = (1 * (2 ** (attempt - 1))) + (random.random())
                time.sleep(backoff_seconds / 10)  # Reduced for testing speed
            else:
                # Success
                self._connected = True
                self.log_calls["connect_success"].append({
                    "device_id": self.device_id, 
                    "session_id": self.session_id
                })
                return True
        
        return False 