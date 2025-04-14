#!/usr/bin/env python3
"""
Test script to create sample tags, credentials, and devices
to verify the tag-based credential matching functionality.
"""

import requests
import json
import time
import sys

# Configuration
API_BASE = "http://localhost:8000/api"
AUTH_ENDPOINT = f"{API_BASE}/auth/login"
TAGS_ENDPOINT = f"{API_BASE}/tags/"
CREDENTIALS_ENDPOINT = f"{API_BASE}/credentials/"
DEVICES_ENDPOINT = f"{API_BASE}/devices/"

# Auth credentials - admin user created by the startup script
USERNAME = "admin"
PASSWORD = "admin123"

# Test data
TAGS = [
    {"name": "datacenter_a", "type": "location"},
    {"name": "datacenter_b", "type": "location"},
    {"name": "core", "type": "role"},
    {"name": "access", "type": "role"},
    {"name": "cisco", "type": "vendor"},
    {"name": "juniper", "type": "vendor"}
]

CREDENTIALS = [
    {
        "username": "cisco_admin",
        "password": "cisco123",
        "priority": 10,
        "description": "Cisco devices admin credential",
        "tags": []  # Will be filled with tag IDs
    },
    {
        "username": "juniper_admin",
        "password": "juniper123",
        "priority": 20,
        "description": "Juniper devices admin credential",
        "tags": []  # Will be filled with tag IDs
    },
    {
        "username": "backup_admin",
        "password": "backup123",
        "priority": 30,
        "description": "Backup admin credential for all devices",
        "tags": []  # Will be filled with tag IDs
    }
]

DEVICES = [
    {
        "hostname": "core-switch-a",
        "ip_address": "192.168.1.1",
        "device_type": "cisco_ios",
        "port": 22,
        "description": "Core Switch in Datacenter A",
        "tags": []  # Will be filled with tag IDs
    },
    {
        "hostname": "access-switch-b",
        "ip_address": "192.168.1.2",
        "device_type": "cisco_ios",
        "port": 22,
        "description": "Access Switch in Datacenter B",
        "tags": []  # Will be filled with tag IDs
    },
    {
        "hostname": "router-juniper",
        "ip_address": "192.168.1.3",
        "device_type": "juniper_junos",
        "port": 22,
        "description": "Juniper Router in Datacenter A",
        "tags": []  # Will be filled with tag IDs
    }
]

def login():
    """Get JWT token for authentication"""
    auth_data = {"username": USERNAME, "password": PASSWORD}
    response = requests.post(AUTH_ENDPOINT, data=auth_data)
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        sys.exit(1)
    
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def create_tags(headers):
    """Create test tags and return a map of tag names to IDs"""
    tag_map = {}
    
    for tag_data in TAGS:
        response = requests.post(TAGS_ENDPOINT, json=tag_data, headers=headers)
        if response.status_code == 201:
            tag = response.json()
            tag_map[tag["name"]] = tag["id"]
            print(f"Created tag: {tag['name']} (ID: {tag['id']})")
        else:
            print(f"Failed to create tag {tag_data['name']}: {response.text}")
    
    return tag_map

def create_credentials(headers, tag_map):
    """Create test credentials with associated tags"""
    credential_map = {}
    
    # Assign tags to credentials
    CREDENTIALS[0]["tags"] = [tag_map["cisco"], tag_map["core"], tag_map["access"]]  # Cisco admin for all Cisco devices
    CREDENTIALS[1]["tags"] = [tag_map["juniper"]]  # Juniper admin for Juniper devices
    CREDENTIALS[2]["tags"] = [tag_map["datacenter_a"], tag_map["datacenter_b"]]  # Backup admin for all datacenters
    
    for cred_data in CREDENTIALS:
        response = requests.post(CREDENTIALS_ENDPOINT, json=cred_data, headers=headers)
        if response.status_code == 201:
            cred = response.json()
            credential_map[cred["username"]] = cred["id"]
            print(f"Created credential: {cred['username']} (ID: {cred['id']})")
        else:
            print(f"Failed to create credential {cred_data['username']}: {response.text}")
    
    return credential_map

def create_devices(headers, tag_map):
    """Create test devices with associated tags"""
    device_map = {}
    
    # Assign tags to devices
    DEVICES[0]["tags"] = [tag_map["datacenter_a"], tag_map["core"], tag_map["cisco"]]  # Cisco core in datacenter A
    DEVICES[1]["tags"] = [tag_map["datacenter_b"], tag_map["access"], tag_map["cisco"]]  # Cisco access in datacenter B
    DEVICES[2]["tags"] = [tag_map["datacenter_a"], tag_map["juniper"]]  # Juniper in datacenter A
    
    for device_data in DEVICES:
        response = requests.post(DEVICES_ENDPOINT, json=device_data, headers=headers)
        if response.status_code == 201:
            device = response.json()
            device_map[device["hostname"]] = device["id"]
            print(f"Created device: {device['hostname']} (ID: {device['id']})")
        else:
            print(f"Failed to create device {device_data['hostname']}: {response.text}")
    
    return device_map

def test_credential_matching(headers, device_map):
    """Test the credential matching endpoint for each device"""
    for hostname, device_id in device_map.items():
        print(f"\nTesting credential matching for device: {hostname} (ID: {device_id})")
        
        response = requests.get(f"{DEVICES_ENDPOINT}{device_id}/credentials", headers=headers)
        if response.status_code == 200:
            credentials = response.json()
            print(f"Found {len(credentials)} matching credentials in priority order:")
            for i, cred in enumerate(credentials, 1):
                print(f"  {i}. {cred['username']} (Priority: {cred['priority']})")
        else:
            print(f"Failed to get matching credentials: {response.text}")

def main():
    print("Starting test data creation...")
    
    # Login to get authentication token
    print("\nLogging in...")
    headers = login()
    
    # Create test data
    print("\nCreating tags...")
    tag_map = create_tags(headers)
    
    print("\nCreating credentials...")
    credential_map = create_credentials(headers, tag_map)
    
    print("\nCreating devices...")
    device_map = create_devices(headers, tag_map)
    
    # Test credential matching
    print("\nTesting credential matching functionality...")
    time.sleep(1)  # Small delay to ensure all data is committed
    test_credential_matching(headers, device_map)
    
    print("\nTest setup complete!")

if __name__ == "__main__":
    main() 