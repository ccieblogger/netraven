#!/usr/bin/env python3
"""
Test script for the Device Gateway.

This script tests the Device Gateway API by connecting to a device
and retrieving its configuration.
"""

import sys
import os
import argparse
import json
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.gateway.client import GatewayClient

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test the Device Gateway')
    parser.add_argument('--host', required=True, help='Device hostname or IP address')
    parser.add_argument('--username', required=True, help='Device username')
    parser.add_argument('--password', required=True, help='Device password')
    parser.add_argument('--device-type', help='Device type (auto-detected if not provided)')
    parser.add_argument('--gateway-url', default='http://localhost:8001', help='Gateway URL')
    parser.add_argument('--command', default='get_running_config', 
                        choices=['get_running_config', 'get_serial_number', 'get_os_info'],
                        help='Command to execute')
    
    args = parser.parse_args()
    
    # Create gateway client
    client = GatewayClient(gateway_url=args.gateway_url)
    
    # Check gateway health
    try:
        health = client.check_health()
        print(f"Gateway health: {health['status']}, version: {health['version']}")
    except Exception as e:
        print(f"Error checking gateway health: {e}")
        return 1
    
    # Connect to device
    try:
        result = client.connect_device(
            host=args.host,
            username=args.username,
            password=args.password,
            device_type=args.device_type
        )
        
        if result['status'] == 'error':
            print(f"Error connecting to device: {result['message']}")
            return 1
        
        print(f"Successfully connected to device: {args.host}")
        
        if result['data'] and result['data'].get('serial_number'):
            print(f"Serial number: {result['data']['serial_number']}")
        
        if result['data'] and result['data'].get('os_info'):
            print(f"OS info: {json.dumps(result['data']['os_info'], indent=2)}")
    
    except Exception as e:
        print(f"Error connecting to device: {e}")
        return 1
    
    # Execute command
    try:
        if args.command == 'get_running_config':
            config = client.get_running_config(
                host=args.host,
                username=args.username,
                password=args.password,
                device_type=args.device_type
            )
            
            if config:
                print(f"Retrieved configuration ({len(config)} bytes)")
                print("First 100 characters:")
                print(config[:100] + "...")
            else:
                print("Failed to retrieve configuration")
                return 1
        
        elif args.command == 'get_serial_number':
            serial = client.get_serial_number(
                host=args.host,
                username=args.username,
                password=args.password,
                device_type=args.device_type
            )
            
            if serial:
                print(f"Serial number: {serial}")
            else:
                print("Failed to retrieve serial number")
                return 1
        
        elif args.command == 'get_os_info':
            os_info = client.get_os_info(
                host=args.host,
                username=args.username,
                password=args.password,
                device_type=args.device_type
            )
            
            if os_info:
                print(f"OS info: {json.dumps(os_info, indent=2)}")
            else:
                print("Failed to retrieve OS info")
                return 1
    
    except Exception as e:
        print(f"Error executing command: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 