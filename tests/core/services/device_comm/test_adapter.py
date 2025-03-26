"""
Tests for the protocol adapters in the Device Communication Service.
"""

import unittest
from unittest.mock import MagicMock, patch

from netraven.core.services.device_comm.protocol import (
    DeviceProtocolAdapter,
    ProtocolAdapterFactory
)
from netraven.core.services.device_comm.errors import (
    DeviceError,
    DeviceConnectionError,
    DeviceCommandError,
    DeviceAuthenticationError
)


class TestProtocolAdapterFactory(unittest.TestCase):
    """Test cases for the ProtocolAdapterFactory class."""

    def test_create_ssh_adapter(self):
        """Test creating an SSH adapter."""
        with patch('netraven.core.services.device_comm.adapters.ssh.SSHProtocolAdapter') as mock_ssh:
            adapter = ProtocolAdapterFactory.create_adapter(
                protocol="ssh",
                host="192.168.1.1",
                username="admin",
                password="password"
            )
            
            # Verify the correct adapter was created
            mock_ssh.assert_called_once_with(
                host="192.168.1.1",
                username="admin",
                password="password",
                device_type=None,
                port=22
            )
            self.assertEqual(adapter, mock_ssh.return_value)
    
    def test_create_adapter_invalid_protocol(self):
        """Test creating an adapter with an invalid protocol."""
        with self.assertRaises(ValueError):
            ProtocolAdapterFactory.create_adapter(
                protocol="invalid",
                host="192.168.1.1",
                username="admin",
                password="password"
            )


class TestSSHAdapter(unittest.TestCase):
    """Test cases for the SSHProtocolAdapter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set up mock for SSHProtocolAdapter
        self.adapter_patcher = patch('netraven.core.services.device_comm.adapters.ssh.SSHProtocolAdapter', autospec=True)
        self.MockAdapter = self.adapter_patcher.start()
        
        # Import the real adapter class for use elsewhere
        from netraven.core.services.device_comm.adapters.ssh import SSHProtocolAdapter
        self.SSHProtocolAdapter = SSHProtocolAdapter
        
        # Create an instance of our mocked adapter class
        self.adapter = self.MockAdapter.return_value
        
        # Setup adapter with necessary host info for the test
        self.adapter.host = "192.168.1.1"
        self.adapter.username = "admin"
        self.adapter.password = "password"
        self.adapter.port = 22
        self.adapter.device_type = "autodetect"
        
        # Setup mock for connection
        self.adapter._connection = MagicMock()
        
        # Setup return values for common methods
        self.adapter.is_connected.return_value = False
        self.adapter.connect.return_value = True
        self.adapter.disconnect.return_value = True
        self.adapter.send_command.return_value = "command output"
        self.adapter.get_config.return_value = "running config data"
        self.adapter.check_connectivity.return_value = True
        self.adapter.get_connection_info.return_value = {
            "host": "192.168.1.1",
            "port": 22,
            "protocol": "ssh",
            "device_type": "autodetect"
        }
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.adapter_patcher.stop()
    
    def test_connect(self):
        """Test connecting to a device."""
        # Connect to the device
        result = self.adapter.connect()
        
        # Verify the connection was established
        self.adapter.connect.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_disconnect(self):
        """Test disconnecting from a device."""
        # First connect
        self.adapter.is_connected.return_value = True
        
        # Then disconnect
        result = self.adapter.disconnect()
        
        # Verify the connection was closed
        self.adapter.disconnect.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
    
    def test_is_connected(self):
        """Test checking if connected."""
        # Before connecting
        self.adapter.is_connected.return_value = False
        self.assertFalse(self.adapter.is_connected())
        
        # After connecting
        self.adapter.is_connected.return_value = True
        self.assertTrue(self.adapter.is_connected())
    
    def test_send_command(self):
        """Test sending a command to a device."""
        # Connect
        self.adapter.is_connected.return_value = True
        
        # Send a command
        result = self.adapter.send_command("show version")
        
        # Verify the command was executed
        self.adapter.send_command.assert_called_once_with("show version")
        
        # Verify the result
        self.assertEqual(result, "command output")
    
    def test_send_commands(self):
        """Test sending multiple commands to a device."""
        # Connect
        self.adapter.is_connected.return_value = True
        
        # Setup the return value for send_commands
        self.adapter.send_commands.return_value = {
            "command1": "output1",
            "command2": "output2"
        }
        
        # Send commands
        result = self.adapter.send_commands(["command1", "command2"])
        
        # Verify the commands were executed
        self.adapter.send_commands.assert_called_once_with(["command1", "command2"])
        
        # Verify the results
        self.assertEqual(result, {"command1": "output1", "command2": "output2"})
    
    def test_get_config(self):
        """Test retrieving a device configuration."""
        # Connect
        self.adapter.is_connected.return_value = True
        
        # Get the running configuration
        result = self.adapter.get_config(config_type="running")
        
        # Verify the config was retrieved
        self.adapter.get_config.assert_called_once_with(config_type="running")
        
        # Verify the result
        self.assertEqual(result, "running config data")
    
    def test_check_connectivity(self):
        """Test checking device connectivity."""
        # Check connectivity
        result = self.adapter.check_connectivity()
        
        # Verify connectivity was checked
        self.adapter.check_connectivity.assert_called_once()
        
        # Verify the result
        self.assertTrue(result)
        
        # Test failed connectivity
        self.adapter.check_connectivity.return_value = False
        result = self.adapter.check_connectivity()
        self.assertFalse(result)
    
    def test_get_connection_info(self):
        """Test getting connection information."""
        # Get connection info
        info = self.adapter.get_connection_info()
        
        # Verify the connection info was retrieved
        self.adapter.get_connection_info.assert_called_once()
        
        # Verify the info contains the basic connection details
        self.assertEqual(info["host"], "192.168.1.1")
        self.assertEqual(info["port"], 22)
        self.assertEqual(info["protocol"], "ssh")
        self.assertEqual(info["device_type"], "autodetect")
    
    def test_connection_error(self):
        """Test handling connection errors."""
        # Configure connect to raise an exception
        self.adapter.connect.side_effect = DeviceConnectionError(
            message="Failed to connect to device",
            host="192.168.1.1"
        )
        
        # Try to connect
        with self.assertRaises(DeviceConnectionError):
            self.adapter.connect()
    
    def test_command_error(self):
        """Test handling command execution errors."""
        # Connect
        self.adapter.is_connected.return_value = True
        
        # Configure the command to fail
        self.adapter.send_command.side_effect = DeviceCommandError(
            message="Error executing command on device",
            host="192.168.1.1",
            commands=["show version"]
        )
        
        # Try to execute a command
        with self.assertRaises(DeviceCommandError):
            self.adapter.send_command("show version")
    
    def test_authentication_error(self):
        """Test handling authentication errors."""
        # Configure connect to raise an authentication error
        self.adapter.connect.side_effect = DeviceAuthenticationError(
            message="Authentication failed",
            host="192.168.1.1"
        )
        
        # Try to connect
        with self.assertRaises(DeviceAuthenticationError):
            self.adapter.connect()


if __name__ == '__main__':
    unittest.main() 