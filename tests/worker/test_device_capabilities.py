import pytest
from unittest.mock import MagicMock, patch
import re

from netraven.worker.device_capabilities import (
    get_device_commands,
    get_command,
    get_command_timeout,
    parse_device_capabilities,
    get_static_capabilities,
    get_command_sequence,
    detect_capabilities_from_device_type,
    adapt_device_commands_by_type,
    detect_error_from_output,
    execute_capability_detection
)

class MockDevice:
    """Mock device class for testing purposes."""
    def __init__(self, device_type='cisco_ios', id=1, hostname='test-device', ip_address='192.168.1.1'):
        self.device_type = device_type
        self.id = id
        self.hostname = hostname
        self.ip_address = ip_address
        self.username = 'test'
        self.password = 'test'


class TestDeviceCommands:
    """Test device command retrieval functions."""
    
    def test_get_device_commands(self):
        """Test that get_device_commands returns the correct commands for a device type."""
        # Test Cisco IOS commands
        cisco_commands = get_device_commands('cisco_ios')
        assert 'show_running' in cisco_commands
        assert cisco_commands['show_running'] == 'show running-config'
        
        # Test Juniper Junos commands
        juniper_commands = get_device_commands('juniper_junos')
        assert 'show_running' in juniper_commands
        assert juniper_commands['show_running'] == 'show configuration | display set'
        
        # Test nonexistent device type returns default commands
        unknown_commands = get_device_commands('nonexistent_type')
        assert 'show_running' in unknown_commands
        assert unknown_commands['show_running'] == 'show running-config'  # Default command
    
    def test_get_command(self):
        """Test that get_command returns the correct specific command."""
        # Test specific commands for different device types
        assert get_command('cisco_ios', 'show_running') == 'show running-config'
        assert get_command('juniper_junos', 'show_running') == 'show configuration | display set'
        assert get_command('paloalto_panos', 'show_version') == 'show system info'
        
        # Test nonexistent command returns None
        assert get_command('cisco_ios', 'nonexistent_command') is None
        assert get_command('default', 'nonexistent_command') is None
    
    def test_get_command_timeout(self):
        """Test that get_command_timeout returns the correct timeout for a command."""
        # Test specific timeouts for different commands and device types
        assert get_command_timeout('cisco_ios', 'show_running') == 60
        assert get_command_timeout('f5_tmsh', 'show_running') == 120  # F5 has longer timeout
        
        # Test default timeout for unknown command
        assert get_command_timeout('cisco_ios', 'unknown_command') == 30  # Default timeout
        
        # Test default device type
        assert get_command_timeout('unknown_device', 'show_running') == 60  # Default device timeout


class TestCapabilityDetection:
    """Test capability detection functions."""
    
    def test_parse_device_capabilities_cisco_ios(self):
        """Test that parse_device_capabilities correctly parses Cisco IOS output."""
        # Sample Cisco IOS version output
        cisco_ios_output = """
        Cisco IOS Software, C3560 Software (C3560-IPSERVICESK9-M), Version 12.2(55)SE, RELEASE SOFTWARE (fc2)
        Copyright (c) 1986-2010 by Cisco Systems, Inc.
        
        ROM: Bootstrap program is C3560 boot loader
        BOOTLDR: C3560 Boot Loader (C3560-HBOOT-M) Version 12.2(44)SE5, RELEASE SOFTWARE (fc1)
        
        Switch uptime is 2 days, 3 hours, 5 minutes
        System returned to ROM by power-on
        System image file is "flash:c3560-ipservicesk9-mz.122-55.SE.bin"
        
        cisco WS-C3560-24PS (PowerPC405) processor (revision E0) with 128MB of memory.
        Processor board ID CAT1033Z1VY
        Last reset from power-on
        """
        
        capabilities = parse_device_capabilities('cisco_ios', cisco_ios_output)
        
        assert capabilities['model'] == 'WS-C3560-24PS'
        assert capabilities['version'] == '12.2(55)SE'
        assert capabilities['serial'] == 'CAT1033Z1VY'
        assert capabilities['platform_subtype'] == 'ios'
        
        # Check static capabilities are included
        assert 'requires_enable' in capabilities
        assert capabilities['requires_enable'] == True
    
    def test_parse_device_capabilities_juniper(self):
        """Test that parse_device_capabilities correctly parses Juniper output."""
        # Sample Juniper version output
        juniper_output = """
        Hostname: router1
        Model: mx240
        JUNOS Base OS boot [19.2R1.8]
        JUNOS Base OS Software Suite [19.2R1.8]
        JUNOS Kernel Software Suite [19.2R1.8]
        JUNOS Crypto Software Suite [19.2R1.8]
        JUNOS Packet Forwarding Engine Support (M/T/EX Common) [19.2R1.8]
        JUNOS Packet Forwarding Engine Support (MX Common) [19.2R1.8]
        JUNOS Online Documentation [19.2R1.8]
        JUNOS py-base-i386 [19.2R1.8]
        
        Chassis                                 JN1234AB1234
        """
        
        capabilities = parse_device_capabilities('juniper_junos', juniper_output)
        
        assert capabilities['model'] == 'mx240'
        assert capabilities['version'] == '19.2R1.8'
        assert capabilities['serial'] == 'JN1234AB1234'
        
        # Check static capabilities are included
        assert 'requires_cli_mode' in capabilities
        assert capabilities['requires_cli_mode'] == True
    
    def test_get_static_capabilities(self):
        """Test that get_static_capabilities returns correct capabilities for a device type."""
        # Test capabilities for different device types
        cisco_caps = get_static_capabilities('cisco_ios')
        assert cisco_caps['requires_enable'] == True
        assert cisco_caps['supports_inventory'] == True
        
        juniper_caps = get_static_capabilities('juniper_junos')
        assert juniper_caps['requires_enable'] == False
        assert juniper_caps['requires_cli_mode'] == True
        
        # Test unknown device type gets default capabilities
        unknown_caps = get_static_capabilities('nonexistent_type')
        assert unknown_caps == get_static_capabilities('default')
    
    def test_get_command_sequence(self):
        """Test that get_command_sequence returns the correct sequence for a device type."""
        # Test Cisco IOS sequence
        cisco_sequence = get_command_sequence('cisco_ios')
        # First command should be enter_enable for Cisco IOS
        assert cisco_sequence[0][0] == 'enter_enable'
        assert cisco_sequence[0][1] == 'enable'
        
        # Test Juniper sequence
        juniper_sequence = get_command_sequence('juniper_junos')
        # First command should be enter_cli for Juniper
        assert juniper_sequence[0][0] == 'enter_cli'
        assert juniper_sequence[0][1] == 'cli'
        
        # Verify running command is always included in sequence
        for device_type in ['cisco_ios', 'juniper_junos', 'paloalto_panos']:
            sequence = get_command_sequence(device_type)
            command_types = [cmd[0] for cmd in sequence]
            assert 'show_running' in command_types
            
    def test_detect_capabilities_from_device_type(self):
        """Test that detect_capabilities_from_device_type returns combined capabilities."""
        # Test capabilities for Cisco IOS
        cisco_capabilities = detect_capabilities_from_device_type('cisco_ios')
        
        # Should include both commands and static capabilities
        assert 'commands' in cisco_capabilities
        assert 'requires_enable' in cisco_capabilities
        assert cisco_capabilities['requires_enable'] == True
        assert 'command_sequence' in cisco_capabilities
        
        # Command sequence should be a list of tuples
        assert isinstance(cisco_capabilities['command_sequence'], list)
        assert all(isinstance(cmd, tuple) for cmd in cisco_capabilities['command_sequence'])
    
    def test_adapt_device_commands_by_type(self):
        """Test that adapt_device_commands_by_type correctly adapts to device object."""
        # Create mock device objects
        cisco_device = MockDevice(device_type='cisco_ios')
        juniper_device = MockDevice(device_type='juniper_junos')
        
        # Test command adaptation for different devices
        cisco_adapted = adapt_device_commands_by_type(cisco_device)
        assert cisco_adapted['device_type'] == 'cisco_ios'
        assert 'commands' in cisco_adapted
        
        juniper_adapted = adapt_device_commands_by_type(juniper_device)
        assert juniper_adapted['device_type'] == 'juniper_junos'
        assert 'commands' in juniper_adapted
        
        # Test with no device_type
        no_type_device = MockDevice()
        delattr(no_type_device, 'device_type')
        no_type_adapted = adapt_device_commands_by_type(no_type_device)
        assert no_type_adapted['device_type'] == 'default'


class TestErrorDetection:
    """Test error detection from command output."""
    
    def test_detect_error_from_output(self):
        """Test that detect_error_from_output correctly identifies errors in command output."""
        # Test Cisco IOS error messages
        cisco_error_output = "% Invalid input detected at '^' marker."
        assert detect_error_from_output('cisco_ios', cisco_error_output) == "Invalid command syntax"
        
        # Test Juniper error messages
        juniper_error_output = "unknown command: show foo"
        assert detect_error_from_output('juniper_junos', juniper_error_output) == "Invalid command syntax"
        
        # Test no error
        no_error_output = "Switch#show version"
        assert detect_error_from_output('cisco_ios', no_error_output) is None
        
        # Test empty output
        assert detect_error_from_output('cisco_ios', '') is None
        assert detect_error_from_output('cisco_ios', None) is None


class TestIntegration:
    """Test integration with netmiko_driver."""
    
    def test_execute_capability_detection(self):
        """Test that execute_capability_detection correctly integrates with run_command."""
        # Create mock device and run_command function
        device = MockDevice(device_type='cisco_ios')
        
        # Sample Cisco IOS output for mocked run_command
        cisco_version_output = """
        Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.1(4)M4, RELEASE SOFTWARE (fc1)
        Technical Support: http://www.cisco.com/techsupport
        Copyright (c) 1986-2012 by Cisco Systems, Inc.
        
        ROM: System Bootstrap, Version 15.0(1r)M15, RELEASE SOFTWARE (fc1)
        
        router uptime is 2 weeks, 3 days, 1 hour, 21 minutes
        System returned to ROM by power-on
        System restarted at 10:37:02 UTC Mon Feb 28 2022
        System image file is "flash:c2900-universalk9-mz.SPA.151-4.M4.bin"
        Last reload type: Normal Reload
        
        cisco CISCO2911/K9 (revision 1.0) with 483328K/45056K bytes of memory.
        Processor board ID FGL1533S0MT
        """
        
        cisco_inventory_output = """
        NAME: "CISCO2911/K9 chassis", DESCR: "CISCO2911/K9 chassis"
        PID: CISCO2911/K9      , VID: V01, SN: FGL1533S0MT
        
        NAME: "module 0", DESCR: "CISCO2911/K9 chassis"
        PID: CISCO2911/K9      , VID: V01, SN: FGL1533S0MT
        
        NAME: "WIC slot 0/1", DESCR: "1-Port Serial"
        PID: HWIC-1T           , VID: V01, SN: FOC123456XY
        
        NAME: "WIC slot 0/2", DESCR: "16 Port Async"
        PID: HWIC-16A          , VID: V01, SN: FOC789012ZQ
        """
        
        # Create a mock run_command function that returns appropriate output
        mock_run_command = MagicMock()
        mock_run_command.side_effect = lambda d, j, command, **kwargs: \
            cisco_version_output if command == 'show version' else \
            cisco_inventory_output if command == 'show inventory' else \
            "show command output"
        
        # Execute capability detection
        capabilities = execute_capability_detection(device, mock_run_command, job_id=1)
        
        # Verify capabilities are detected
        assert capabilities['model'] == 'CISCO2911/K9'
        assert capabilities['version'] == '15.1(4)M4'
        assert capabilities['serial'] == 'FGL1533S0MT'
        assert capabilities['platform_subtype'] == 'ios'
        
        # Verify inventory output is stored
        assert 'inventory_output' in capabilities
        assert cisco_inventory_output in capabilities['inventory_output']
        
        # Verify static capabilities are included
        assert 'requires_enable' in capabilities
        assert capabilities['requires_enable'] == True
        
        # Verify run_command was called with expected arguments
        assert mock_run_command.call_count >= 2  # At least version and inventory
        mock_run_command.assert_any_call(device, 1, command='show version')
        mock_run_command.assert_any_call(device, 1, command='show inventory')
    
    def test_execute_capability_detection_with_exception(self):
        """Test that execute_capability_detection handles exceptions gracefully."""
        # Create mock device
        device = MockDevice(device_type='cisco_ios')
        
        # Create a mock run_command function that raises an exception
        mock_run_command = MagicMock()
        mock_run_command.side_effect = Exception("Connection error")
        
        # Execute capability detection with failing command
        capabilities = execute_capability_detection(device, mock_run_command, job_id=1)
        
        # Verify we still get static capabilities
        assert 'device_type' in capabilities
        assert capabilities['device_type'] == 'cisco_ios'
        assert 'requires_enable' in capabilities
        assert capabilities['requires_enable'] == True
        
        # Verify dynamic capabilities are missing
        assert 'version' not in capabilities or capabilities['version'] == 'Unknown'
        assert 'inventory_output' not in capabilities 