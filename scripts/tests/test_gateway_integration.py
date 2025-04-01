#!/usr/bin/env python3
"""
Integration test script for the Device Gateway.

This script performs comprehensive testing of the Device Gateway API,
including error handling, performance, and security features.
"""

import sys
import os
import argparse
import json
import time
import concurrent.futures
from typing import Dict, Any, List, Tuple
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.gateway.client import GatewayClient
from netraven.gateway.utils import sanitize_log_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gateway_integration_test")

def test_health_check(client: GatewayClient) -> bool:
    """Test the health check endpoint."""
    try:
        logger.info("Testing health check endpoint...")
        health = client.check_health()
        logger.info(f"Health check result: {health}")
        return health["status"] == "healthy"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def test_device_connection(
    client: GatewayClient,
    host: str,
    username: str,
    password: str,
    device_type: str = None
) -> bool:
    """Test device connection."""
    try:
        logger.info(f"Testing connection to device {host}...")
        result = client.connect_device(
            host=host,
            username=username,
            password=password,
            device_type=device_type
        )
        logger.info(f"Connection result: {sanitize_log_data(result)}")
        return result["status"] == "success"
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def test_command_execution(
    client: GatewayClient,
    host: str,
    username: str,
    password: str,
    device_type: str = None
) -> bool:
    """Test command execution."""
    commands = ["get_running_config", "get_serial_number", "get_os_info"]
    success = True
    
    for command in commands:
        try:
            logger.info(f"Testing command execution: {command}...")
            result = client.execute_command(
                host=host,
                username=username,
                password=password,
                device_type=device_type,
                command=command
            )
            
            if result["status"] != "success":
                logger.error(f"Command {command} failed: {result['message']}")
                success = False
            else:
                logger.info(f"Command {command} succeeded")
                
                # For running config, check if we got actual content
                if command == "get_running_config" and not result["data"]:
                    logger.error("Running config is empty")
                    success = False
        except Exception as e:
            logger.error(f"Command {command} failed with exception: {e}")
            success = False
    
    return success

def test_error_handling(client: GatewayClient) -> bool:
    """Test error handling."""
    tests = [
        # Invalid host
        {
            "host": "invalid-host-that-does-not-exist.local",
            "username": "test",
            "password": "test",
            "expected_status": "error"
        },
        # Invalid credentials
        {
            "host": "192.168.1.31",  # Use a real host that exists
            "username": "invalid_user",
            "password": "invalid_password",
            "expected_status": "error"
        },
        # Invalid command
        {
            "host": "192.168.1.31",  # Use a real host that exists
            "username": "admin",
            "password": "Password1",
            "command": "invalid_command",
            "expected_status": "error"
        }
    ]
    
    success = True
    
    for test in tests:
        try:
            logger.info(f"Testing error handling: {test}...")
            
            if test.get("command"):
                result = client.execute_command(
                    host=test["host"],
                    username=test["username"],
                    password=test["password"],
                    command=test["command"]
                )
            else:
                result = client.connect_device(
                    host=test["host"],
                    username=test["username"],
                    password=test["password"]
                )
            
            if result["status"] != test["expected_status"]:
                logger.error(f"Error handling test failed: expected {test['expected_status']}, got {result['status']}")
                success = False
            else:
                logger.info(f"Error handling test succeeded: {result['message']}")
        except Exception as e:
            # For connection errors, exceptions are expected
            logger.info(f"Got expected exception: {e}")
    
    return success

def test_performance(
    client: GatewayClient,
    host: str,
    username: str,
    password: str,
    device_type: str = None,
    num_requests: int = 5
) -> bool:
    """Test performance with multiple concurrent requests."""
    logger.info(f"Testing performance with {num_requests} concurrent requests...")
    
    start_time = time.time()
    success_count = 0
    
    # Function to execute in parallel
    def execute_request(i: int) -> bool:
        try:
            logger.info(f"Executing request {i}...")
            result = client.connect_device(
                host=host,
                username=username,
                password=password,
                device_type=device_type
            )
            return result["status"] == "success"
        except Exception as e:
            logger.error(f"Request {i} failed: {e}")
            return False
    
    # Execute requests in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        futures = [executor.submit(execute_request, i) for i in range(num_requests)]
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                success_count += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Performance test completed in {duration:.2f} seconds")
    logger.info(f"Success rate: {success_count}/{num_requests} ({success_count/num_requests*100:.2f}%)")
    
    # Consider the test successful if at least 80% of requests succeeded
    return success_count >= num_requests * 0.8

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Integration test for the Device Gateway')
    parser.add_argument('--host', required=True, help='Device hostname or IP address')
    parser.add_argument('--username', required=True, help='Device username')
    parser.add_argument('--password', required=True, help='Device password')
    parser.add_argument('--device-type', help='Device type (auto-detected if not provided)')
    parser.add_argument('--gateway-url', default='http://localhost:8001', help='Gateway URL')
    parser.add_argument('--skip-performance', action='store_true', help='Skip performance tests')
    
    args = parser.parse_args()
    
    # Create gateway client
    client = GatewayClient(gateway_url=args.gateway_url)
    
    # Run tests
    tests = [
        ("Health Check", lambda: test_health_check(client)),
        ("Device Connection", lambda: test_device_connection(
            client, args.host, args.username, args.password, args.device_type
        )),
        ("Command Execution", lambda: test_command_execution(
            client, args.host, args.username, args.password, args.device_type
        )),
        ("Error Handling", lambda: test_error_handling(client))
    ]
    
    if not args.skip_performance:
        tests.append(("Performance", lambda: test_performance(
            client, args.host, args.username, args.password, args.device_type
        )))
    
    # Run tests and collect results
    results = []
    all_passed = True
    
    for name, test_func in tests:
        logger.info(f"Running test: {name}")
        try:
            passed = test_func()
            results.append((name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {name} failed with exception: {e}")
            results.append((name, False))
            all_passed = False
    
    # Print summary
    logger.info("Test Results:")
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        logger.info(f"  {name}: {status}")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main()) 