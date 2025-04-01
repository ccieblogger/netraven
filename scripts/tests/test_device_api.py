#!/usr/bin/env python3
import requests
import json
import sys

# API endpoint
API_URL = "http://localhost:8000/api/devices"

# Your auth token (you'll need to get this from your browser after logging in)
# Check localStorage in your browser dev tools
TOKEN = input("Enter your JWT token from browser (localStorage.access_token): ")

# Test device data
test_device = {
    "hostname": "router_test",
    "ip_address": "192.168.1.10",
    "device_type": "cisco_ios",
    "port": 22,
    "description": "Test device for API debugging",
    "username": "admin",
    "password": "cisco123",
    "enabled": True
}

# Headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

try:
    # Create device
    print(f"Attempting to create device with data: {json.dumps(test_device, indent=2)}")
    response = requests.post(API_URL, json=test_device, headers=headers)
    
    # Print status code and response
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 201:
        print("Device created successfully!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Failed to create device. Error: {response.text}")
        
        # If it's a validation error, print more details
        if response.status_code == 422:
            try:
                error_detail = response.json().get('detail', '')
                print(f"Validation errors: {json.dumps(error_detail, indent=2)}")
            except:
                print("Could not parse validation error details")
                
except Exception as e:
    print(f"Exception occurred: {str(e)}") 