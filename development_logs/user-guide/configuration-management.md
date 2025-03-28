# Configuration Management Guide

## Introduction

This guide explains how to effectively manage network device configurations using NetRaven. Configuration management is a core function of NetRaven that allows you to backup, restore, compare, and deploy configurations across your network infrastructure.

## Purpose

By following this guide, you will learn how to:
- Create and manage configuration backups
- Compare configuration versions to identify changes
- Deploy configurations to devices
- Establish configuration templates
- Set up configuration compliance policies

## Prerequisites

Before working with configuration management features, ensure you have:
- Administrator or operator access to NetRaven
- Network devices added to the inventory
- Appropriate credentials for accessing devices
- Basic understanding of the device configuration syntax

## Configuration Backup

### Manual Backup

To manually create a configuration backup:

1. Navigate to **Devices** > **Device List**
2. Select the device you want to backup
3. Click the **Actions** button and select **Backup Configuration**
4. Choose the backup type:
   - **Running Configuration**: The active configuration on the device
   - **Startup Configuration**: The configuration that will be used at next reboot
   - **Full Backup**: Both running and startup configurations
5. Click **Start Backup**
6. The backup job will be initiated and you can monitor its progress in the **Jobs** section

### Scheduled Backups

To set up automated configuration backups:

1. Navigate to **Settings** > **Backup Schedules**
2. Click **Add Backup Schedule**
3. Configure the schedule settings:
   - **Name**: A descriptive name for the schedule
   - **Devices**: Select individual devices or device groups
   - **Backup Type**: Running, Startup, or Full
   - **Schedule**: Define frequency (Daily, Weekly, Monthly)
   - **Time**: Set the time for the backup to run
   - **Retention**: Number of backups to retain per device
4. Click **Save Schedule**

### Viewing Backup History

To view configuration backup history:

1. Navigate to **Devices** > **Device List**
2. Select the device you want to view backups for
3. Click on the **Backups** tab
4. The list shows all backups with timestamps, types, and status
5. Click on a backup entry to view details or perform actions

## Configuration Comparison

### Comparing Configuration Versions

To compare different versions of a device's configuration:

1. Navigate to **Devices** > **Device List**
2. Select the device you want to analyze
3. Click on the **Backups** tab
4. Select two backups using the checkboxes
5. Click **Compare Selected**
6. The comparison view will highlight:
   - Added lines (green)
   - Removed lines (red)
   - Modified lines (yellow)

### Comparing Configurations Across Devices

To compare configurations between different devices:

1. Navigate to **Tools** > **Configuration Comparison**
2. In the **First Device** dropdown, select the source device
3. Select the backup version for the first device
4. In the **Second Device** dropdown, select the target device
5. Select the backup version for the second device
6. Click **Compare**
7. Review the differences highlighted in the comparison view

## Configuration Deployment

### Restoring a Previous Configuration

To restore a device to a previous configuration:

1. Navigate to **Devices** > **Device List**
2. Select the device you want to restore
3. Click on the **Backups** tab
4. Find the backup version you want to restore
5. Click the **Actions** button and select **Restore**
6. Confirm the restore operation
7. Monitor the restore job in the **Jobs** section

### Creating Configuration Deployments

To deploy a new or modified configuration:

1. Navigate to **Configurations** > **Deployments**
2. Click **New Deployment**
3. Configure the deployment:
   - **Name**: A descriptive name for the deployment
   - **Description**: Optional details about the purpose
   - **Devices**: Select target devices
   - **Configuration**: Upload a configuration file, paste configuration text, or select a template
   - **Validation**: Enable/disable pre-deployment validation
   - **Backup**: Enable automatic backup before deployment
   - **Rollback**: Enable automatic rollback on failure
4. Click **Save Draft** or **Deploy Now**

### Scheduling Configuration Deployments

To schedule a configuration deployment for a future time:

1. Follow steps 1-3 from "Creating Configuration Deployments"
2. In the deployment settings, enable **Schedule Deployment**
3. Set the deployment date and time
4. Complete the remaining configuration options
5. Click **Save Schedule**

## Configuration Templates

### Creating Configuration Templates

To create reusable configuration templates:

1. Navigate to **Configurations** > **Templates**
2. Click **New Template**
3. Configure the template:
   - **Name**: A descriptive name for the template
   - **Description**: Purpose and usage information
   - **Device Types**: Compatible device types
   - **Template Content**: The configuration template text
   - **Variables**: Define customizable variables with default values
4. Click **Save Template**

### Using Variables in Templates

Templates can include variables that are replaced during deployment:

```
hostname {{hostname}}
ntp server {{ntp_server}}
username {{admin_username}} privilege 15 secret {{admin_password}}
```

When using a template for deployment, you'll be prompted to provide values for each variable.

### Deploying with Templates

To deploy a configuration using a template:

1. Navigate to **Configurations** > **Deployments**
2. Click **New Deployment**
3. In the **Configuration Source** section, select **Use Template**
4. Choose the template from the dropdown
5. Fill in values for all template variables
6. Complete the remaining deployment settings
7. Click **Deploy Now** or **Save Draft**

## Configuration Compliance

### Creating Compliance Policies

To create configuration compliance policies:

1. Navigate to **Compliance** > **Policies**
2. Click **New Policy**
3. Configure the policy:
   - **Name**: A descriptive name for the policy
   - **Description**: Purpose and requirements
   - **Device Types**: Applicable device types
   - **Rules**: Add compliance rules (see below)
4. Click **Save Policy**

### Compliance Rule Types

NetRaven supports several types of compliance rules:

- **Pattern Match**: Check if a configuration contains a specified pattern
- **Pattern Absence**: Verify a pattern does not exist in the configuration
- **Command Present**: Ensure specific commands are present
- **Value Match**: Check if a configuration parameter has a specific value
- **Script**: Use a custom script to evaluate compliance

### Assigning Policies to Devices

To assign compliance policies to devices:

1. Navigate to **Compliance** > **Policies**
2. Select the policy you want to assign
3. Click **Assign to Devices**
4. Select individual devices or device groups
5. Click **Assign**

### Running Compliance Checks

To run a compliance check:

1. Navigate to **Compliance** > **Dashboard**
2. Click **Run Compliance Check**
3. Select the devices or device groups to check
4. Select the policies to evaluate
5. Click **Start Check**
6. Review the results in the compliance dashboard

## Troubleshooting

### Common Issues

- **Failed Backups**: Check device connectivity and credentials
- **Deployment Failures**: Review error messages and device logs
- **Template Errors**: Verify variable syntax and device compatibility

### Backup History Clean-up

If you need to clean up old backups:

1. Navigate to **Settings** > **Backup Management**
2. Use the filters to locate old or unwanted backups
3. Select the backups to remove
4. Click **Delete Selected**

## Related Documentation

- [Device Management Guide](./device-management.md)
- [Backup Storage Configuration](../admin-guide/storage-configuration.md)
- [Troubleshooting Guide](../admin-guide/troubleshooting.md)
- [Configuration Templates Reference](../reference/configuration-templates.md) 