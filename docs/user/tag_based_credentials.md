# Tag-Based Credential System in NetRaven

## Overview

NetRaven uses a tag-based system to associate credentials with devices. This approach provides flexibility and simplifies credential management by allowing multiple credentials to be associated with a device through shared tags.

## How Tag-Based Credential Matching Works

Instead of manually assigning a specific credential to each device, NetRaven uses tags as the matching mechanism:

1. **Tags are applied to both devices and credentials**
2. **Devices match with credentials that share at least one tag**
3. **When multiple credentials match, they are tried in priority order**

This approach enables powerful and flexible credential management, especially in large networks with different device types and access requirements.

## Example Scenario

Consider the following setup:

| Device | Tags |
|--------|------|
| Core Switch A | datacenter_a, cisco, core |
| Access Switch B | datacenter_b, cisco, access |
| Router C | datacenter_a, juniper |

| Credential | Priority | Tags |
|------------|----------|------|
| cisco_admin | 10 | cisco |
| juniper_admin | 20 | juniper |
| backup_admin | 30 | datacenter_a, datacenter_b |

In this scenario:

- **Core Switch A** matches with:
  1. `cisco_admin` (priority 10) - due to the "cisco" tag
  2. `backup_admin` (priority 30) - due to the "datacenter_a" tag

- **Access Switch B** matches with:
  1. `cisco_admin` (priority 10) - due to the "cisco" tag
  2. `backup_admin` (priority 30) - due to the "datacenter_b" tag

- **Router C** matches with:
  1. `juniper_admin` (priority 20) - due to the "juniper" tag
  2. `backup_admin` (priority 30) - due to the "datacenter_a" tag

When NetRaven needs to connect to a device, it will try the matching credentials in order of priority (lower numbers first) until a successful connection is established.

## Managing Tag-Based Credentials

### Creating and Assigning Tags

1. Navigate to the **Tags** section in the NetRaven UI
2. Create tags that represent logical groupings (locations, device types, roles, etc.)
3. When creating or editing a device or credential, assign the appropriate tags

### Understanding Credential Priority

Each credential has a priority value (lower number = higher priority):

- When multiple credentials match a device, the one with the lowest priority number is tried first
- If that credential fails, the next credential in priority order is tried
- This continues until a successful connection is established or all credentials are exhausted

### Viewing Matching Credentials

To see which credentials match a specific device:

1. Go to the **Devices** page
2. In the device list, hover over the credential count to see all matching credentials and their priority

## Best Practices

1. **Create a logical tag taxonomy**:
   - Location tags (datacenter_a, branch_office, etc.)
   - Role tags (core, distribution, access, etc.)
   - Vendor/OS tags (cisco, juniper, arista, etc.)

2. **Set appropriate credential priorities**:
   - Lower numbers (higher priority) for primary credentials
   - Higher numbers (lower priority) for backup/fallback credentials

3. **Use tag combinations for specificity**:
   - Apply multiple tags to both devices and credentials
   - The more specific the tag combination, the more precise the credential matching

4. **Consider creating a fallback credential**:
   - Create a low-priority credential with a broad tag that matches many devices
   - This ensures devices always have at least one credential to try 