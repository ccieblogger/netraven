#!/usr/bin/env python3
"""
Test script for the Device Gateway authentication.

This script tests the authentication features of the Device Gateway API.
"""

import sys
import os
import argparse
import json
import requests
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from netraven.gateway.client import GatewayClient

def test_api_key_auth(gateway_url: str, api_key: str) -> bool:
    """Test API key authentication."""
    print(f"Testing API key authentication with key: {api_key[:5]}...")
    
    # Create client with API key
    client = GatewayClient(gateway_url=gateway_url, api_key=api_key)
    
    # Test health check (no auth required)
    try:
        health = client.check_health()
        print(f"Health check successful: {health}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    # Test protected endpoint
    try:
        # Use a dummy device that doesn't need to exist
        result = client.connect_device(
            host="test-device.local",
            username="test",
            password="test"
        )
        
        # We expect this to fail with a connection error, not an auth error
        if result["status"] == "error" and "Failed to connect" in result["message"]:
            print("API key authentication successful (got expected connection error)")
            return True
        else:
            print(f"Unexpected result: {result}")
            return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"API key authentication failed: {e}")
            return False
        else:
            print(f"Got unexpected error: {e}")
            return False
    except Exception as e:
        print(f"Error testing API key authentication: {e}")
        return False

def test_token_auth(gateway_url: str, api_key: str) -> bool:
    """Test token authentication."""
    print(f"Testing token authentication with key: {api_key[:5]}...")
    
    # Create client
    client = GatewayClient(gateway_url=gateway_url)
    
    # Get token
    try:
        token_data = client.get_token(api_key=api_key)
        print(f"Got token: {token_data['access_token'][:10]}...")
    except Exception as e:
        print(f"Failed to get token: {e}")
        return False
    
    # Test with token
    # Note: The current implementation uses API key auth, not token auth
    # This is a placeholder for future token-based authentication
    return True

def test_invalid_auth(gateway_url: str) -> bool:
    """Test invalid authentication."""
    print("Testing invalid authentication...")
    
    # Test with invalid API key
    try:
        headers = {"X-API-Key": "invalid-api-key"}
        response = requests.post(
            f"{gateway_url}/connect",
            headers=headers,
            json={
                "host": "test-device.local",
                "username": "test",
                "password": "test"
            }
        )
        
        if response.status_code == 401:
            print("Invalid API key test passed (got 401 Unauthorized)")
            return True
        else:
            print(f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error testing invalid authentication: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test the Device Gateway authentication')
    parser.add_argument('--gateway-url', default='http://localhost:8001', help='Gateway URL')
    parser.add_argument('--api-key', default='netraven-api-key', help='API key for authentication')
    
    args = parser.parse_args()
    
    # Run tests
    tests = [
        ("API Key Authentication", lambda: test_api_key_auth(args.gateway_url, args.api_key)),
        ("Token Authentication", lambda: test_token_auth(args.gateway_url, args.api_key)),
        ("Invalid Authentication", lambda: test_invalid_auth(args.gateway_url))
    ]
    
    # Run tests and collect results
    results = []
    all_passed = True
    
    for name, test_func in tests:
        print(f"\nRunning test: {name}")
        try:
            passed = test_func()
            results.append((name, passed))
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"Test {name} failed with exception: {e}")
            results.append((name, False))
            all_passed = False
    
    # Print summary
    print("\nTest Results:")
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main()) 