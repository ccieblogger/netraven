"""
Mock data generation for tests.

This module provides functions for generating mock data for testing.
"""

import random
import uuid
import ipaddress
import string
import datetime


def generate_device_data(custom_data=None):
    """
    Generate random device data for testing.
    
    Args:
        custom_data (dict, optional): Custom data to override defaults.
        
    Returns:
        dict: Device data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Generate a random IP address
    ip_int = random.randint(0x0A000000, 0x0AFFFFFF)  # Range from 10.0.0.0 to 10.255.255.255
    ip_address = str(ipaddress.IPv4Address(ip_int))
    
    # Device types commonly used
    device_types = [
        "cisco_ios", "cisco_nxos", "cisco_asa", "cisco_xr", 
        "juniper_junos", "arista_eos", "fortinet", "paloalto_panos"
    ]
    
    # Generate base data
    data = {
        "hostname": f"test-device-{unique_id}",
        "ip_address": ip_address,
        "device_type": random.choice(device_types),
        "username": "testuser",
        "password": "testpassword",
        "enable_password": "testenable",
        "description": f"Test device generated for automated testing {unique_id}",
        "port": random.choice([22, 23]),
        "is_active": random.choice([True, False]),
        "tags": []
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data


def generate_user_data(custom_data=None, admin=False):
    """
    Generate random user data for testing.
    
    Args:
        custom_data (dict, optional): Custom data to override defaults.
        admin (bool, optional): Whether to generate an admin user. Defaults to False.
        
    Returns:
        dict: User data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Random first and last names
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]
    
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    
    # Generate base data
    data = {
        "username": f"testuser-{unique_id}",
        "email": f"testuser-{unique_id}@example.com",
        "password": "TestPassword123!",
        "first_name": first_name,
        "last_name": last_name,
        "is_admin": admin,
        "is_active": True,
        "scopes": ["devices:read", "devices:write"] if not admin else None
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data


def generate_tag_data(custom_data=None):
    """
    Generate random tag data for testing.
    
    Args:
        custom_data (dict, optional): Custom data to override defaults.
        
    Returns:
        dict: Tag data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Random colors
    colors = [
        "#FF5733", "#33FF57", "#3357FF", "#F3FF33", 
        "#FF33F3", "#33FFF3", "#F333FF", "#FFA233"
    ]
    
    # Generate base data
    data = {
        "name": f"test-tag-{unique_id}",
        "description": f"Test tag for automated testing {unique_id}",
        "color": random.choice(colors)
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data


def generate_audit_log_data(custom_data=None):
    """
    Generate random audit log data for testing.
    
    Args:
        custom_data (dict, optional): Custom data to override defaults.
        
    Returns:
        dict: Audit log data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Random actions
    actions = ["create", "update", "delete", "view"]
    resource_types = ["device", "user", "tag", "backup", "config"]
    
    # Generate a random timestamp within the last 30 days
    now = datetime.datetime.now()
    past = now - datetime.timedelta(days=30)
    random_timestamp = past + datetime.timedelta(
        seconds=random.randint(0, int((now - past).total_seconds()))
    )
    
    # Generate base data
    action = random.choice(actions)
    resource_type = random.choice(resource_types)
    
    data = {
        "id": f"log-{unique_id}",
        "timestamp": random_timestamp.isoformat(),
        "user_id": f"user-{uuid.uuid4().hex[:8]}",
        "username": f"testuser-{uuid.uuid4().hex[:6]}",
        "action": action,
        "resource_type": resource_type,
        "resource_id": f"{resource_type}-{uuid.uuid4().hex[:8]}",
        "details": {
            "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data


def generate_backup_data(device_id=None, custom_data=None):
    """
    Generate random backup data for testing.
    
    Args:
        device_id (str, optional): Device ID for the backup.
        custom_data (dict, optional): Custom data to override defaults.
        
    Returns:
        dict: Backup data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Random content
    config_lines = [
        "hostname test-device",
        "interface GigabitEthernet0/0",
        " ip address 192.168.1.1 255.255.255.0",
        " no shutdown",
        "interface GigabitEthernet0/1",
        " ip address 10.0.0.1 255.255.255.0",
        " shutdown",
        "ip route 0.0.0.0 0.0.0.0 192.168.1.254",
        "line vty 0 4",
        " login local",
        " transport input ssh"
    ]
    
    # Generate a random timestamp within the last 30 days
    now = datetime.datetime.now()
    past = now - datetime.timedelta(days=30)
    random_timestamp = past + datetime.timedelta(
        seconds=random.randint(0, int((now - past).total_seconds()))
    )
    
    # Generate device ID if not provided
    if not device_id:
        device_id = f"device-{uuid.uuid4().hex[:8]}"
    
    # Generate base data
    data = {
        "id": f"backup-{unique_id}",
        "device_id": device_id,
        "timestamp": random_timestamp.isoformat(),
        "backup_type": random.choice(["running-config", "startup-config"]),
        "content": "\n".join(config_lines),
        "status": random.choice(["completed", "failed", "in_progress"]),
        "size_bytes": random.randint(500, 10000)
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data


def generate_tag_rule_data(tag_id=None, custom_data=None):
    """
    Generate random tag rule data for testing.
    
    Args:
        tag_id (str, optional): Tag ID for the rule.
        custom_data (dict, optional): Custom data to override defaults.
        
    Returns:
        dict: Tag rule data
    """
    # Generate a unique ID
    unique_id = uuid.uuid4().hex[:8]
    
    # Rule field options
    fields = ["hostname", "ip_address", "device_type", "description"]
    operators = ["equals", "contains", "startswith", "endswith", "regex"]
    
    # Generate tag ID if not provided
    if not tag_id:
        tag_id = f"tag-{uuid.uuid4().hex[:8]}"
    
    # Generate a random field and operator
    field = random.choice(fields)
    operator = random.choice(operators)
    
    # Generate a value based on the field and operator
    if field == "hostname":
        value = f"test-device" if operator == "contains" else f"test-device-{unique_id}"
    elif field == "ip_address":
        ip_int = random.randint(0x0A000000, 0x0AFFFFFF)
        value = str(ipaddress.IPv4Address(ip_int))
    elif field == "device_type":
        device_types = ["cisco_ios", "cisco_nxos", "juniper_junos", "arista_eos"]
        value = random.choice(device_types)
    else:
        value = f"test-description-{unique_id}"
    
    # Generate base data
    data = {
        "name": f"test-rule-{unique_id}",
        "description": f"Test rule for automated testing {unique_id}",
        "tag_id": tag_id,
        "is_active": random.choice([True, False]),
        "rule_criteria": {
            "field": field,
            "operator": operator,
            "value": value
        }
    }
    
    # Override with custom data if provided
    if custom_data:
        data.update(custom_data)
    
    return data 