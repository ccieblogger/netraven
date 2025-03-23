# Managing Devices in NetRaven

## Introduction

This guide covers all aspects of device management in NetRaven, including adding, organizing, monitoring, and troubleshooting network devices. Effective device management is essential for maintaining your network inventory and ensuring successful configuration backups.

## Purpose

By following this guide, you will learn how to:
- Add and configure devices in NetRaven
- Organize devices using groups and tags
- Monitor device status and connectivity
- Troubleshoot common device issues

## Prerequisites

Before managing devices, ensure you have:
- Administrator or Device Manager role in NetRaven
- Network connectivity to the devices you want to manage
- Valid authentication credentials for each device
- Knowledge of device types and access methods

## Adding Devices

### Adding a Single Device

1. Navigate to **Devices** > **Device List**
2. Click the **Add Device** button
3. Fill in the device details:

   ```
   Name: A descriptive name for the device
   IP Address/Hostname: Device's IP address or resolvable hostname
   Device Type: Select the appropriate device type from the dropdown
   Description: (Optional) Additional information about the device
   ```

4. Configure the connection settings:

   ```
   Port: SSH port (default: 22)
   Connection Timeout: Time in seconds before connection attempts time out
   Connection Retries: Number of connection retry attempts
   ```

5. Configure authentication:

   ```
   Username: Account with sufficient privileges
   Password: Account password
   Enable Password: (If required by the device type)
   ```

6. Click **Test Connection** to verify that NetRaven can connect to the device

7. Click **Save** to add the device

### Bulk Import Devices

To add multiple devices at once:

1. Navigate to **Devices** > **Device List**
2. Click the **Import Devices** button
3. Choose one of the following options:

   #### CSV Import
   
   1. Download the CSV template
   2. Fill in the device details in the CSV file
   3. Upload the completed CSV file
   4. Review the import preview
   5. Click **Import** to add the devices

   #### Network Discovery
   
   1. Enter the IP range to scan (CIDR notation)
   2. Select the discovery method (ICMP, SNMP, SSH)
   3. Configure discovery credentials
   4. Click **Start Discovery**
   5. Review discovered devices
   6. Select devices to import
   7. Click **Import Selected** to add the devices

## Organizing Devices

### Device Groups

Groups help organize devices logically, such as by location, function, or department:

1. Navigate to **Devices** > **Device Groups**
2. Click **Add Group**
3. Enter the group details:

   ```
   Name: A descriptive name for the group
   Description: (Optional) Purpose of the group
   Parent Group: (Optional) Select a parent group if using a hierarchical structure
   ```

4. Click **Save** to create the group
5. To add devices to the group:
   - Navigate to the group details page
   - Click **Add Devices**
   - Select devices from the list
   - Click **Add Selected** to add them to the group

### Device Tags

Tags are labels you can apply to devices for flexible categorization:

1. Navigate to **Administration** > **Tags**
2. Click **Add Tag**
3. Configure the tag:

   ```
   Name: A short, descriptive name
   Color: Select a color for visual identification
   Description: (Optional) Purpose of the tag
   ```

4. Click **Save** to create the tag
5. To apply tags to devices:
   - Navigate to **Devices** > **Device List**
   - Select one or more devices
   - Click **Actions** > **Apply Tags**
   - Select the tags to apply
   - Click **Apply** to tag the devices

## Device Management

### Viewing Device Details

To view detailed information about a device:

1. Navigate to **Devices** > **Device List**
2. Click on the device name
3. The device details page shows:
   - Basic device information
   - Connection status
   - Backup history
   - Configuration change history
   - Applied tags and group membership

### Editing Device Configuration

To modify a device's configuration:

1. Navigate to **Devices** > **Device List**
2. Find the device and click the **Edit** icon
3. Update the device details as needed
4. Click **Save** to apply the changes

### Removing Devices

To remove a device from NetRaven:

1. Navigate to **Devices** > **Device List**
2. Select one or more devices to remove
3. Click **Actions** > **Delete**
4. Confirm the deletion
   - Note: Device backup history can be retained or deleted based on your selection

## Device Actions

### Manual Backup

To manually trigger a configuration backup:

1. Navigate to **Devices** > **Device List**
2. Find the device and click **Actions** > **Backup Now**
3. The backup job will start and display progress
4. Once complete, the backup will be visible in the **Backups** tab

### Testing Connectivity

To verify connectivity to a device:

1. Navigate to **Devices** > **Device List**
2. Find the device and click **Actions** > **Test Connection**
3. NetRaven will attempt to connect to the device and report the status
4. The test results will show:
   - Connection success/failure
   - Response time
   - Authentication status
   - Any error messages if the test fails

### Running Device Commands

For supported device types, you can run commands:

1. Navigate to **Devices** > **Device List**
2. Find the device and click **Actions** > **Run Command**
3. Enter the command to execute
4. Click **Run** to execute the command
5. The command output will be displayed in real-time

### Configuration Snapshots

To take an on-demand configuration snapshot:

1. Navigate to the device details page
2. Click the **Snapshot** button
3. Select the configuration type (running, startup, etc.)
4. Add a description for the snapshot
5. Click **Create Snapshot**
6. The snapshot will appear in the Snapshots tab

## Device Monitoring

### Status Dashboard

The device status dashboard provides a real-time overview:

1. Navigate to **Dashboard** > **Device Status**
2. View the status summary showing:
   - Total devices count
   - Online/offline device counts
   - Backup status summary
   - Recent connectivity issues

### Status Alerts

Configure alerts for device status changes:

1. Navigate to **Settings** > **Alerts**
2. Click **Add Alert Rule**
3. Configure the alert conditions:
   ```
   Name: Descriptive name for the alert
   Condition: Device status changes to offline
   Devices: All devices or select specific devices/groups
   Notification: Email, Slack, or other configured notification methods
   ```
4. Click **Save** to create the alert

## Troubleshooting Devices

### Connectivity Issues

If a device shows as offline or unreachable:

1. Verify network connectivity:
   - Check if the device is reachable from the NetRaven server using ping
   - Ensure no firewalls are blocking the required ports

2. Verify authentication:
   - Check if credentials are correct
   - Ensure the user has sufficient privileges
   - Check if the device has reached its maximum simultaneous sessions limit

3. Check connection logs:
   - Navigate to **Devices** > device details > **Logs**
   - Review recent connection attempts and error messages

### Backup Failures

If device backups are failing:

1. Check the backup failure message:
   - Navigate to **Backups** > **Failed Backups**
   - Click on the failed backup to see the detailed error

2. Common issues include:
   - Timeout: The device is taking too long to respond
   - Authentication: Incorrect credentials or privilege level
   - Command error: The backup command is not supported or has syntax errors
   - Storage: The backup storage is full or inaccessible

3. Perform a test connection to verify basic connectivity

4. Check device compatibility:
   - Verify the device model is supported
   - Check if the OS version is compatible
   - Ensure the correct device type is selected

## Best Practices

Follow these guidelines for effective device management:

1. **Standardize device naming**: Use a consistent naming convention for all devices
2. **Use groups and tags**: Organize devices logically for easier management
3. **Validate new devices**: Always test connection before adding to production
4. **Document device details**: Use the description field for important device information
5. **Regular audits**: Periodically verify the device inventory for accuracy
6. **Credential management**: Update credentials when they change and use credential management tools when possible
7. **Access control**: Limit who can add and modify device information

## Related Documentation

- [Configuration Backups](./backups.md)
- [Device Groups and Organization](./device-groups.md)
- [Scheduled Tasks](./scheduled-tasks.md)
- [Troubleshooting Guide](../admin-guide/troubleshooting.md) 