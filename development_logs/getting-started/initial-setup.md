# NetRaven Initial Setup

## Introduction

This guide covers the initial setup steps required after installing NetRaven. These steps will help you configure the system for production use, secure your installation, and prepare for adding devices.

## Purpose

By following this guide, you will:
- Configure essential system settings
- Secure your NetRaven installation
- Set up storage for backups
- Configure notification settings
- Prepare the system for adding devices

## Prerequisites

Before proceeding, ensure you have:
- Completed the [NetRaven installation](./installation.md)
- Administrator access to the system
- Basic understanding of your network environment

## Step 1: First Login and Password Change

1. Access the web interface at `http://your-server:8080`

2. Log in with the default administrator credentials:
   - Username: `admin`
   - Password: `adminpass123` (or the custom password if you specified one during installation)

3. Change the default password immediately:
   - Click on your username in the top-right corner
   - Select **Profile** from the dropdown menu
   - Click the **Change Password** button
   - Enter the current password and your new secure password
   - Click **Save**

## Step 2: Configure System Settings

Navigate to the **Settings** page from the main menu to configure the following:

### General Settings

1. **System Name**: Set a meaningful name for your NetRaven instance
2. **System URL**: Configure the base URL where NetRaven is accessible (important for emails and notifications)
3. **Time Zone**: Set the appropriate time zone for your location
4. **Date Format**: Configure your preferred date/time format

### Security Settings

1. **Session Timeout**: Set how long inactive sessions remain valid (default: 24 hours)
2. **Password Policy**: Configure password requirements:
   - Minimum length (recommended: 12 characters)
   - Complexity requirements (uppercase, lowercase, numbers, special characters)
   - Password expiration (if required by your organization)
3. **Failed Login Attempts**: Configure account lockout after multiple failed attempts

## Step 3: Configure Backup Storage

NetRaven supports multiple storage backends for device configuration backups:

### Local File Storage (Default)

The default storage uses the local filesystem within the Docker container:

1. Navigate to **Settings** > **Backup Storage**
2. Ensure **Storage Type** is set to `local`
3. Set the base path if needed (default: `/app/data/backups`)

### S3 Compatible Storage (Recommended for Production)

For production environments, it's recommended to use S3-compatible storage:

1. Navigate to **Settings** > **Backup Storage**
2. Change **Storage Type** to `s3`
3. Configure the S3 settings:
   ```
   Bucket Name: your-bucket-name
   Region: us-east-1 (or your preferred region)
   Access Key: your-access-key
   Secret Key: your-secret-key
   Path Prefix: netraven/ (optional)
   ```
4. Click **Test Connection** to verify the settings
5. Click **Save** to apply the changes

## Step 4: Configure Email Notifications

Email notifications allow NetRaven to alert you about important events:

1. Navigate to **Settings** > **Notifications**
2. Enable email notifications
3. Configure SMTP settings:
   ```
   SMTP Server: smtp.example.com
   SMTP Port: 587
   Use TLS: Yes
   SMTP Username: your-username
   SMTP Password: your-password
   From Email: netraven@example.com
   From Name: NetRaven System
   ```
4. Configure notification preferences:
   - Backup failures
   - Device connectivity issues
   - Security alerts
   - System updates
5. Click **Send Test Email** to verify the settings
6. Click **Save** to apply the changes

## Step 5: Configure Authentication Integration (Optional)

For larger environments, you may want to integrate with an external authentication system:

### LDAP Integration

1. Navigate to **Settings** > **Authentication**
2. Enable LDAP authentication
3. Configure LDAP settings:
   ```
   LDAP Server: ldap.example.com
   LDAP Port: 389
   Use SSL/TLS: Yes
   Bind DN: cn=netraven,ou=service,dc=example,dc=com
   Bind Password: your-bind-password
   User Search Base: ou=users,dc=example,dc=com
   User Search Filter: (sAMAccountName={0})
   Group Search Base: ou=groups,dc=example,dc=com
   ```
4. Configure group mappings:
   - Admin Group DN: `cn=network-admins,ou=groups,dc=example,dc=com`
   - User Group DN: `cn=network-users,ou=groups,dc=example,dc=com`
5. Click **Test Connection** to verify the settings
6. Click **Save** to apply the changes

## Step 6: Create User Accounts

Before adding devices, create user accounts for your team:

1. Navigate to **Administration** > **Users**
2. Click **Add User**
3. Fill in the user details:
   - Username
   - Email
   - Password
   - User Role (Admin, User, Read-Only)
4. Click **Save** to create the user

## Step 7: Configure Tags (Optional)

Tags help organize devices and apply policies:

1. Navigate to **Administration** > **Tags**
2. Click **Add Tag**
3. Create commonly used tags such as:
   - Location tags (e.g., "Datacenter", "Branch Office")
   - Role tags (e.g., "Core", "Distribution", "Access")
   - Vendor tags (e.g., "Cisco", "Juniper", "Arista")
4. For each tag, configure:
   - Name
   - Color
   - Description

## Step 8: Configure Tag Rules (Optional)

Tag rules automatically assign tags to devices based on criteria:

1. Navigate to **Administration** > **Tag Rules**
2. Click **Add Rule**
3. Configure the rule:
   - Name: "Cisco Devices"
   - Tag: select the "Cisco" tag
   - Criteria: `device_type contains "cisco"`
4. Click **Save** to create the rule

## Security Recommendations

For production deployments, consider these additional security measures:

1. **Use HTTPS**: Configure a reverse proxy (Nginx, Apache) with SSL/TLS
2. **Network Security**: Restrict access to the NetRaven services using firewalls
3. **API Tokens**: Generate API tokens with limited permissions for integration
4. **Regular Backups**: Set up database backups
5. **Secret Key**: Change the default `TOKEN_SECRET_KEY` in your environment variables

## Next Steps

After completing the initial setup:

- Proceed to [Adding Your First Device](../user-guide/managing-devices.md)
- Set up [Scheduled Backups](../user-guide/backups.md)
- Configure [Monitoring and Alerts](../admin-guide/monitoring.md)

## Related Documentation

- [User Management](../admin-guide/user-management.md)
- [Security Best Practices](../admin-guide/security.md)
- [Configuration Reference](../reference/configuration-options.md) 