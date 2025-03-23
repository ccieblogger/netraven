# Configuration Backups in NetRaven

## Introduction

This guide covers the configuration backup features in NetRaven, including scheduling backups, managing backup storage, comparing configurations, and restoring configurations. Configuration backups are a core feature of NetRaven, allowing you to track changes, recover from errors, and maintain a history of your network devices.

## Purpose

By following this guide, you will learn how to:
- Configure backup settings
- Schedule regular backups
- Compare configuration versions
- Restore previous configurations
- Manage backup storage

## Prerequisites

Before working with backups, ensure you have:
- Devices properly configured in NetRaven
- Administrator or Backup Manager role
- Storage configured for backups
- Understanding of your device configuration types

## Backup Types

NetRaven supports various types of configuration backups:

### Running Configuration

- The active configuration currently running on the device
- Command used depends on device type (e.g., `show running-config` for Cisco IOS)
- Most frequently backed up configuration type

### Startup Configuration

- The configuration that will be loaded on next device boot
- Important to back up periodically to ensure it matches running config
- Command used depends on device type (e.g., `show startup-config` for Cisco IOS)

### Full Backup

- For supported devices, includes both running and startup configurations
- May include additional files depending on device type
- Provides most complete recovery option

## Configuring Backup Settings

### Global Backup Settings

1. Navigate to **Settings** > **Backup Settings**
2. Configure the following options:

   ```
   Default Backup Type: Running Configuration
   Backup Retention Period: 90 days (or as needed)
   Enable Automatic Backup Pruning: Yes
   Store Configuration Differences: Yes
   Backup Storage Location: Local Storage (or configured S3 storage)
   ```

3. Click **Save** to apply the settings

### Device-Specific Backup Settings

To override global settings for specific devices:

1. Navigate to **Devices** > **Device List**
2. Click on the device name to view details
3. Go to the **Backup Settings** tab
4. Enable **Override Global Settings**
5. Configure device-specific settings:

   ```
   Backup Type: (Select appropriate type)
   Custom Backup Command: (If needed for special devices)
   Pre/Post Backup Commands: (Optional commands to run before/after backup)
   ```

6. Click **Save** to apply the settings

## Running Manual Backups

### Single Device Backup

1. Navigate to **Devices** > **Device List**
2. Find the device and click **Actions** > **Backup Now**
3. Select the backup type (if different from default)
4. Add a description (optional)
5. Click **Start Backup**
6. The backup job will run and show progress

### Bulk Device Backup

To back up multiple devices at once:

1. Navigate to **Devices** > **Device List**
2. Select multiple devices using the checkboxes
3. Click **Actions** > **Backup Selected**
4. Choose backup options:

   ```
   Backup Type: Running Configuration (or other)
   Parallel Execution: Yes (runs multiple backups simultaneously)
   Description: (Optional label for this backup set)
   ```

5. Click **Start Backup**
6. Monitor progress on the Jobs page

## Scheduling Backups

Regular scheduled backups ensure you maintain an up-to-date history of configurations.

### Creating a Backup Schedule

1. Navigate to **Settings** > **Backup Schedules**
2. Click **Add Schedule**
3. Configure the schedule details:

   ```
   Name: Descriptive name (e.g., "Daily Router Backups")
   Description: Purpose of this schedule
   Active: Yes (to enable this schedule)
   ```

4. Set the schedule frequency:

   ```
   Frequency: Daily, Weekly, Monthly, or Custom
   Time: When backups should run (preferably during low-traffic periods)
   Days: Which days to run (for Weekly or Custom)
   ```

5. Select devices to include:

   ```
   All Devices: No (unless you want to back up everything)
   Device Groups: Select relevant groups
   Individual Devices: Select specific devices
   Device Tags: Select devices with specific tags
   ```

6. Configure backup options:

   ```
   Backup Type: Running Configuration (or as needed)
   Parallel Execution: Yes (recommended for many devices)
   Retry Failed: Yes
   Max Retries: 3
   ```

7. Click **Save** to create the schedule

### Managing Schedules

To modify or disable an existing schedule:

1. Navigate to **Settings** > **Backup Schedules**
2. Find the schedule in the list
3. Click **Edit** to modify or toggle the **Active** switch to enable/disable
4. Make any needed changes
5. Click **Save** to apply changes

## Viewing Backup History

### All Backups

1. Navigate to **Backups** > **Backup History**
2. View the list of all backups with:
   - Date and time
   - Device name
   - Backup type
   - Status (successful, failed)
   - Size
   - User who initiated (if manual)

3. Use filters to narrow down the list:
   - Date range
   - Device or group
   - Status
   - Backup type

### Device-Specific Backups

1. Navigate to **Devices** > **Device List**
2. Click on the device name
3. Go to the **Backups** tab
4. View all backup history for this specific device

## Working with Backup Content

### Viewing a Configuration

1. Navigate to **Backups** > **Backup History**
2. Find the backup you want to view
3. Click on the backup date/time
4. The configuration viewer will open showing:
   - Full configuration text
   - Syntax highlighting (for supported device types)
   - Line numbers
   - Search functionality

### Comparing Configurations

To identify changes between backup versions:

1. Navigate to **Backups** > **Backup History**
2. Find a backup and click **Compare**
3. Select another backup version to compare against
4. The comparison view will show:
   - Side-by-side comparison
   - Highlighted differences
   - Added lines (green)
   - Removed lines (red)
   - Modified lines (yellow)

### Exporting Backups

To export backup data:

1. Navigate to **Backups** > **Backup History**
2. Select one or more backups
3. Click **Export**
4. Choose export options:
   - Format: Text, JSON, or ZIP (for multiple backups)
   - Include metadata: Yes/No
5. Click **Download** to save the export file

## Configuration Restoration

### Preparing for Restoration

Before restoring a configuration:

1. Verify device connectivity
2. Consider creating a new backup of the current state
3. Schedule a maintenance window if in production
4. Ensure you have console access for recovery if needed

### Restoring a Configuration

1. Navigate to **Backups** > **Backup History**
2. Find the backup version you want to restore
3. Click **Actions** > **Restore Configuration**
4. Review the warning message
5. Choose restoration options:
   ```
   Restoration Method: Full Replace or Merge
   Verify After Restore: Yes (recommended)
   Save to Startup Config: Yes/No
   ```
6. Click **Proceed** to start the restoration
7. Monitor the restoration job progress

### Post-Restoration Verification

After restoring a configuration:

1. Wait for the device to fully apply the configuration
2. Check for any error messages during restoration
3. Verify connectivity to the device
4. Test critical functionality
5. Run a new backup to confirm the state

## Backup Storage Management

### Storage Backends

NetRaven supports multiple storage backends:

#### Local File Storage

- Default storage mechanism
- Files stored on the NetRaven server
- Simple but limited by server disk space

To configure:
1. Navigate to **Settings** > **Backup Storage**
2. Select **Local Storage**
3. Configure the path and retention settings
4. Click **Save**

#### S3 Compatible Storage

- Recommended for production environments
- Scalable and resilient
- Works with AWS S3, MinIO, and other S3-compatible services

To configure:
1. Navigate to **Settings** > **Backup Storage**
2. Select **S3 Storage**
3. Configure the connection:
   ```
   Bucket Name: your-bucket-name
   Region: us-east-1 (or your region)
   Access Key: Your access key
   Secret Key: Your secret key
   Path Prefix: netraven/ (optional)
   ```
4. Click **Test Connection**
5. Click **Save** if the test is successful

### Storage Monitoring

To monitor backup storage usage:

1. Navigate to **Settings** > **Backup Storage**
2. View the storage dashboard showing:
   - Total storage used
   - Usage by device
   - Growth trend
   - Estimated storage needs

### Backup Pruning

To manage backup retention:

1. Navigate to **Settings** > **Backup Settings**
2. Configure retention policies:
   ```
   Automatic Pruning: Enabled
   Default Retention Period: 90 days
   Keep All Backups Newer Than: 7 days
   Keep One Backup Per: Day (for backups 7-30 days old)
   Keep One Backup Per: Week (for backups 30-90 days old)
   Keep One Backup Per: Month (for backups older than 90 days)
   ```
3. Click **Save** to apply the policy
4. To manually prune backups, click **Run Pruning Now**

## Troubleshooting Backup Issues

### Failed Backups

If backups are failing:

1. Navigate to **Backups** > **Failed Backups**
2. Review the error message for the failed backup
3. Common issues include:
   - Device connectivity problems
   - Authentication failures
   - Timeout (device too slow to respond)
   - Command syntax errors
   - Storage backend issues

4. Check the device connectivity by running a test connection
5. Verify credentials are still valid
6. Check if the backup command is appropriate for the device type

### Stuck Backup Jobs

If backup jobs appear stuck:

1. Navigate to **Administration** > **Jobs**
2. Find the stuck backup job
3. Click **Cancel** to terminate the job
4. If jobs frequently get stuck, check:
   - Device response times
   - Network connectivity
   - Timeout settings

## Best Practices

1. **Regular schedules**: Set up daily backups for critical devices
2. **Diverse timing**: Stagger backup schedules to avoid overloading the network
3. **Verification**: Periodically verify that backups are restorable
4. **Redundancy**: Use S3 or other resilient storage for production environments
5. **Monitoring**: Set up alerts for backup failures
6. **Retention policies**: Define appropriate retention based on your change frequency and compliance requirements
7. **Change tracking**: Use the comparison feature to monitor configuration changes
8. **Documentation**: Add descriptions to manual backups for context

## Related Documentation

- [Managing Devices](./managing-devices.md)
- [Scheduled Tasks](./scheduled-tasks.md)
- [Storage Configuration](../admin-guide/storage-configuration.md)
- [Backup Automation API](../developer-guide/api-reference.md) 