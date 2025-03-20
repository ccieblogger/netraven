# Credential Store System

The Credential Store provides a unified interface for securely managing device credentials, with support for credential retrieval by tag and tracking of credential usage success/failure rates.

## Overview

The credential store was designed to solve several key challenges:

1. **Centralized Management**: Manage all credentials in a single secure location, rather than storing them directly in device records.
2. **Tag-Based Organization**: Organize credentials by tags (like device type, location, or role) for easier management.
3. **Retry Mechanism**: Automatically try alternative credentials when a connection fails.
4. **Success Tracking**: Track which credentials work best for different types of devices.
5. **Encryption**: Secure credentials using standard encryption.

## Components

### Core Classes

- `Credential`: Represents a set of credentials with username, password, and tracking information.
- `CredentialTag`: Associates credentials with tags, including priority and success rates.
- `CredentialStore`: Manages storage and retrieval of credentials, with encryption support.

### Integration with Device Connector

The credential store integrates with both the core `DeviceConnector` and the job-specific `JobDeviceConnector` classes:

- `DeviceConnector.connect_with_credential_id()`: Connect using a specific credential ID.
- `DeviceConnector.connect_with_tag()`: Connect using credentials associated with a tag ID.
- `JobDeviceConnector`: Enhanced with support for tag-based authentication and comprehensive retry mechanisms.

## Using the Credential Store

### Tag-Based Authentication

Devices can now be configured to use tag-based authentication instead of storing credentials directly:

1. Create credentials in the credential store
2. Associate credentials with tags
3. Associate devices with those tags
4. Devices will automatically use the associated credentials when connecting

### API Changes

The device creation and update APIs now support a `tag_ids` parameter for specifying credential-related tags:

```json
{
  "hostname": "router1.example.com",
  "ip_address": "192.168.1.1",
  "device_type": "cisco_ios",
  "tag_ids": ["6f9d32a0-a9fb-4a89-8e6c-fb25c9966641"]
}
```

### Setting Up the Credential Store

Run the setup script to initialize the credential store:

```bash
python scripts/setup_credential_store.py
```

This will:
1. Create a SQLite database for the credential store
2. Add sample credentials (Admin, Backup, Monitor)
3. Create sample tags (Routers, Switches, Firewalls)
4. Associate credentials with tags at different priority levels

## Database Structure

The credential store uses three tables:

1. **credentials**: Stores credential information:
   - id (primary key)
   - name
   - username
   - password (encrypted)
   - description
   - created_at, updated_at
   - success_count, failure_count

2. **tags**: Stores tag information:
   - id (primary key)
   - name
   - description
   - color
   - created_at, updated_at

3. **credential_tags**: Links credentials to tags:
   - credential_id (foreign key)
   - tag_id (foreign key)
   - priority (for ordering credential attempts)
   - success_count, failure_count (specific to this credential-tag combination)

## Credential Priority System

When connecting to a device using a tag, credentials are tried in order of their priority:

1. Credentials with higher priority values are tried first
2. If a connection fails, the next highest priority credential is tried
3. Success and failure rates are tracked both at the credential level and credential-tag level

## Security Considerations

- Passwords are encrypted in the credential store using Fernet symmetric encryption
- Database access should be restricted to authorized personnel
- Password rotation policies should be implemented separately 