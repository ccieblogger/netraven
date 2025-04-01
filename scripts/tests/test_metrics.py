#!/usr/bin/env python3
"""
Test script for the Device Gateway API metrics endpoint.

This script tests the metrics endpoint of the Device Gateway API
by making requests and verifying the metrics are being collected.
"""

import sys
import os
import argparse
import json
import time
import requests
from typing import Dict, Any, List, Optional


def test_metrics_endpoint(gateway_url: str, api_key: str) -> bool:
    """
    Test the metrics endpoint of the gateway API.
    
    Args:
        gateway_url: URL of the gateway API
        api_key: API key for authentication
        
    Returns:
        True if the test passed, False otherwise
    """
    print(f"\n=== Testing metrics endpoint ===")
    
    # Make a request to the metrics endpoint
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{gateway_url}/metrics", headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Error: Failed to get metrics. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    # Parse the metrics
    try:
        metrics = response.json()
        print(f"Metrics retrieved successfully:")
        print(json.dumps(metrics, indent=2))
        return True
    except json.JSONDecodeError:
        print(f"Error: Failed to parse metrics response as JSON")
        print(f"Response: {response.text}")
        return False


def generate_test_traffic(gateway_url: str, api_key: str, num_requests: int = 5) -> bool:
    """
    Generate test traffic to the gateway API.
    
    Args:
        gateway_url: URL of the gateway API
        api_key: API key for authentication
        num_requests: Number of requests to make
        
    Returns:
        True if all requests were successful, False otherwise
    """
    print(f"\n=== Generating test traffic ({num_requests} requests) ===")
    
    # Make requests to various endpoints
    endpoints = [
        "/health",
        "/metrics",
        "/token"
    ]
    
    headers = {"X-API-Key": api_key}
    success_count = 0
    
    for i in range(num_requests):
        # Choose an endpoint
        endpoint = endpoints[i % len(endpoints)]
        
        # Make the request
        if endpoint == "/token":
            # Token endpoint requires a POST request with an API key
            response = requests.post(
                f"{gateway_url}{endpoint}",
                json={"api_key": api_key}
            )
        else:
            # Other endpoints use GET with the API key in the header
            response = requests.get(f"{gateway_url}{endpoint}", headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            print(f"Request {i+1}/{num_requests} to {endpoint}: Success")
            success_count += 1
        else:
            print(f"Request {i+1}/{num_requests} to {endpoint}: Failed ({response.status_code})")
            print(f"Response: {response.text}")
    
    # Generate an error request
    print("\n=== Generating an error request ===")
    response = requests.get(f"{gateway_url}/nonexistent-endpoint", headers=headers)
    print(f"Error request: {response.status_code}")
    
    success_rate = success_count / num_requests * 100
    print(f"\nSuccess rate: {success_rate:.1f}% ({success_count}/{num_requests})")
    
    return success_count == num_requests


def compare_metrics(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    """
    Compare metrics before and after test traffic.
    
    Args:
        before: Metrics before test traffic
        after: Metrics after test traffic
        
    Returns:
        True if metrics changed as expected, False otherwise
    """
    print("\n=== Comparing metrics ===")
    
    # Check if total_requests increased
    before_requests = before.get("total_requests", 0)
    after_requests = after.get("total_requests", 0)
    
    if after_requests <= before_requests:
        print(f"Error: Total requests did not increase")
        print(f"Before: {before_requests}, After: {after_requests}")
        return False
    
    print(f"Total requests increased: {before_requests} -> {after_requests}")
    
    # Check if successful_requests increased
    before_success = before.get("successful_requests", 0)
    after_success = after.get("successful_requests", 0)
    
    if after_success <= before_success:
        print(f"Error: Successful requests did not increase")
        print(f"Before: {before_success}, After: {after_success}")
        return False
    
    print(f"Successful requests increased: {before_success} -> {after_success}")
    
    # Check if error_count increased
    before_errors = before.get("error_count", 0)
    after_errors = after.get("error_count", 0)
    
    if after_errors <= before_errors:
        print(f"Warning: Error count did not increase as expected")
        print(f"Before: {before_errors}, After: {after_errors}")
    else:
        print(f"Error count increased: {before_errors} -> {after_errors}")
    
    return True


def main():
    """Main function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test the Device Gateway API metrics")
    parser.add_argument("--url", default="http://localhost:8001", help="URL of the gateway API")
    parser.add_argument("--api-key", default="netraven-api-key", help="API key for authentication")
    args = parser.parse_args()
    
    # Test the metrics endpoint
    print(f"Testing metrics for gateway at {args.url}")
    
    # Get initial metrics
    headers = {"X-API-Key": args.api_key}
    response = requests.get(f"{args.url}/metrics", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Failed to get initial metrics. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    initial_metrics = response.json()
    print("Initial metrics retrieved successfully")
    
    # Generate test traffic
    if not generate_test_traffic(args.url, args.api_key):
        print("Warning: Some test requests failed")
    
    # Wait a moment for metrics to update
    time.sleep(1)
    
    # Get updated metrics
    response = requests.get(f"{args.url}/metrics", headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Failed to get updated metrics. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    updated_metrics = response.json()
    print("Updated metrics retrieved successfully")
    
    # Compare metrics
    if compare_metrics(initial_metrics, updated_metrics):
        print("\n✅ Metrics test passed: Metrics are being collected correctly")
        sys.exit(0)
    else:
        print("\n❌ Metrics test failed: Metrics are not being collected correctly")
        sys.exit(1)


if __name__ == "__main__":
    main() 