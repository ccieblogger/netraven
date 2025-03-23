# NetRaven Quick Start Guide

## Introduction

This quick start guide provides the fastest path to get NetRaven running and managing your first network device. Follow these steps to quickly experience the core functionality of NetRaven.

## Purpose

This guide will help you:
- Install NetRaven using Docker
- Add your first network device
- Run your first configuration backup
- Navigate the main interface

## Prerequisites

Before starting, ensure you have:
- A Linux server with Docker and Docker Compose installed
- At least 4GB of RAM and 2 CPU cores
- A network device that supports SSH
- Basic familiarity with Docker and networking concepts

## Step 1: Install NetRaven

The fastest way to get started is using Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/netraven.git
   cd netraven
   ```

2. Start NetRaven:
   ```bash
   docker-compose up -d
   ```

3. Wait for all services to start (this may take 1-2 minutes)

4. Access the web interface at `http://your-server:8080`

## Step 2: First Login

1. Log in with the default administrator credentials:
   - Username: `admin`
   - Password: `adminpass123`

2. You'll be prompted to change the default password. Choose a secure password and save it.

## Step 3: Add Your First Device

1. From the dashboard, click **Add Device** or navigate to **Devices** > **Add Device**

2. Enter the device details:
   ```
   Name: RouterA
   IP Address: 192.168.1.1 (use your device's IP)
   Device Type: cisco_ios (or select appropriate type)
   Username: your-device-username
   Password: your-device-password
   Enable Password: your-enable-password (if required)
   ```

3. Click **Test Connection** to verify connectivity

4. Click **Save** to add the device

## Step 4: Run Your First Backup

1. From the Devices list, locate your newly added device

2. Click the **Actions** button and select **Backup Now**

3. The system will:
   - Connect to your device
   - Download the running configuration
   - Store it in the configured backup storage
   - Display the status in real-time

4. Once complete, click on the device name to view details

5. Navigate to the **Backups** tab to see your first configuration backup

## Step 5: Explore the Configuration

1. From the device's Backups tab, click on the most recent backup

2. The configuration viewer will display the full device configuration

3. You can:
   - Search for specific text using the search box
   - Toggle syntax highlighting
   - Compare with previous backups (if available)
   - Download the configuration file

## Step 6: Schedule Regular Backups

1. Navigate to **Settings** > **Backup Schedules**

2. Click **Add Schedule**

3. Configure a basic schedule:
   ```
   Name: Daily Backups
   Frequency: Daily
   Time: 2:00 AM
   Devices: All Devices (or select specific devices)
   ```

4. Click **Save** to create the schedule

## Step 7: Explore the Dashboard

1. Return to the dashboard by clicking **Dashboard** in the main menu

2. The dashboard displays:
   - Device status summary
   - Recent backups
   - Failed backups (if any)
   - System health metrics

## Next Steps

Now that you have NetRaven running with your first device:

- Add more devices by following Step 3
- Explore [device groups](../user-guide/device-groups.md) to organize your inventory
- Learn about [configuration comparison](../user-guide/config-diff.md) to track changes
- Set up [notifications](../user-guide/notifications.md) for important events
- Configure [LDAP/Active Directory](../admin-guide/authentication.md) for user authentication

## Troubleshooting

If you encounter issues:

- Check device connectivity using standard tools (ping, SSH)
- Verify credentials are correct
- Consult the [Troubleshooting Guide](../admin-guide/troubleshooting.md)
- Review logs in Docker: `docker-compose logs -f`

## Related Documentation

- [Complete Installation Guide](./installation.md)
- [Initial Setup Guide](./initial-setup.md)
- [Managing Devices](../user-guide/managing-devices.md)
- [Configuration Management](../user-guide/configuration-management.md) 