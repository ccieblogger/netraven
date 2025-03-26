"""
Tests for the error classes in the Device Communication Service.
"""

import unittest

from netraven.core.services.device_comm.errors import (
    DeviceError,
    DeviceErrorType,
    DeviceConnectionError,
    DeviceCommandError,
    DeviceAuthenticationError,
    PoolExhaustedError
)


class TestDeviceCommErrors(unittest.TestCase):
    """Test cases for the device communication error classes."""
    
    def test_device_error(self):
        """Test the base DeviceError class."""
        error = DeviceError(
            error_type=DeviceErrorType.UNKNOWN_ERROR,
            message="Test error"
        )
        self.assertEqual(str(error), "[unknown_error] Test error")
        
        # Test with additional details
        error = DeviceError(
            error_type=DeviceErrorType.UNKNOWN_ERROR,
            message="Test error",
            details={"key": "value"}
        )
        self.assertEqual(str(error), "[unknown_error] Test error")
        self.assertEqual(error.details, {"key": "value"})
        
        # Test with device_id and host
        error = DeviceError(
            error_type=DeviceErrorType.UNKNOWN_ERROR,
            message="Test error",
            device_id="device1",
            host="192.168.1.1"
        )
        self.assertEqual(
            str(error),
            "[unknown_error] Test error (device: device1) (host: 192.168.1.1)"
        )
    
    def test_device_connection_error(self):
        """Test the DeviceConnectionError class."""
        error = DeviceConnectionError(
            message="Failed to connect to device",
            host="192.168.1.1"
        )
        self.assertEqual(
            str(error),
            "[connection_error] Failed to connect to device (host: 192.168.1.1)"
        )
        self.assertEqual(error.host, "192.168.1.1")
        
        # Test with additional details
        error = DeviceConnectionError(
            message="Failed to connect to device",
            host="192.168.1.1",
            details={"port": 22}
        )
        self.assertEqual(error.error_type, DeviceErrorType.CONNECTION_ERROR)
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.details, {"port": 22})
    
    def test_device_command_error(self):
        """Test the DeviceCommandError class."""
        error = DeviceCommandError(
            message="Error executing command on device",
            host="192.168.1.1",
            commands=["show version"]
        )
        self.assertEqual(
            str(error),
            "[command_error] Error executing command on device (host: 192.168.1.1)"
        )
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.commands, ["show version"])
        
        # Test with additional details
        error = DeviceCommandError(
            message="Error executing command on device",
            host="192.168.1.1",
            commands=["show version"],
            details={"exit_code": 1}
        )
        self.assertEqual(error.error_type, DeviceErrorType.COMMAND_ERROR)
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.commands, ["show version"])
        self.assertEqual(error.details, {"exit_code": 1})
    
    def test_device_authentication_error(self):
        """Test the DeviceAuthenticationError class."""
        error = DeviceAuthenticationError(
            message="Authentication failed",
            host="192.168.1.1",
            details={"username": "admin"}
        )
        self.assertEqual(
            str(error),
            "[authentication_error] Authentication failed (host: 192.168.1.1)"
        )
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.details, {"username": "admin"})
        
        # Test with device_id
        error = DeviceAuthenticationError(
            message="Authentication failed",
            device_id="device1",
            host="192.168.1.1",
            details={"username": "admin"}
        )
        self.assertEqual(
            str(error),
            "[authentication_error] Authentication failed (device: device1) (host: 192.168.1.1)"
        )
        self.assertEqual(error.error_type, DeviceErrorType.AUTHENTICATION_ERROR)
        self.assertEqual(error.device_id, "device1")
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.details, {"username": "admin"})
    
    def test_pool_exhausted_error(self):
        """Test the PoolExhaustedError class."""
        error = PoolExhaustedError(
            message="Connection pool is full"
        )
        self.assertEqual(
            str(error),
            "[pool_exhausted] Connection pool is full"
        )
        
        # Test with host information
        error = PoolExhaustedError(
            message="Maximum connections per host reached",
            host="192.168.1.1"
        )
        self.assertEqual(
            str(error),
            "[pool_exhausted] Maximum connections per host reached (host: 192.168.1.1)"
        )
        self.assertEqual(error.host, "192.168.1.1")
        
        # Test with additional details
        error = PoolExhaustedError(
            message="Connection pool is full",
            host="192.168.1.1",
            details={"limit": 5, "current": 5}
        )
        self.assertEqual(error.error_type, DeviceErrorType.POOL_EXHAUSTED)
        self.assertEqual(error.host, "192.168.1.1")
        self.assertEqual(error.details, {"limit": 5, "current": 5})


if __name__ == '__main__':
    unittest.main() 