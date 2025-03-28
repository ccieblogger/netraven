# User Troubleshooting Guide

## Introduction

This guide helps NetRaven users diagnose and resolve common issues they may encounter while using the platform. It provides step-by-step troubleshooting procedures for various problems related to the web interface, device connections, configuration management, backups, and other key features.

## Purpose

By following this guide, you will be able to:
- Identify and resolve common user interface issues
- Troubleshoot device connectivity problems
- Fix configuration backup and deployment errors
- Resolve authentication and access problems
- Know when to escalate issues to administrators

## Web Interface Issues

### Login Problems

**Issue**: Unable to log in to the NetRaven web interface.

**Troubleshooting Steps**:

1. **Verify Credentials**
   - Ensure you're using the correct username and password
   - Check if Caps Lock is enabled
   - Clear browser cache and cookies

2. **Password Reset**
   - Click "Forgot Password" on the login screen
   - Follow the email instructions to reset your password
   - If you don't receive a reset email, contact your administrator

3. **Account Lockout**
   - After multiple failed attempts, your account may be locked
   - Wait for the lockout period to expire (typically 30 minutes)
   - Contact your administrator for immediate unlock

### Page Load Issues

**Issue**: Web interface loads slowly or displays errors.

**Troubleshooting Steps**:

1. **Browser Troubleshooting**
   - Clear browser cache and cookies
   - Try a different browser
   - Disable browser extensions temporarily

2. **Check Network Connection**
   - Verify your network connection is stable
   - Check if you can access other websites
   - Try connecting from a different network if possible

3. **Browser Console Errors**
   - Open browser developer tools (F12 in most browsers)
   - Check the Console tab for error messages
   - Report specific errors to your administrator

### Display Formatting Problems

**Issue**: Web interface appears broken or incorrectly formatted.

**Troubleshooting Steps**:

1. **Zoom Level**
   - Reset your browser zoom level to 100% (Ctrl+0)
   - Verify display resolution meets minimum requirements

2. **Browser Compatibility**
   - Ensure you're using a supported browser:
     - Chrome (latest 2 versions)
     - Firefox (latest 2 versions)
     - Edge (latest 2 versions)
     - Safari (latest 2 versions)

3. **CSS/JavaScript Issues**
   - Force refresh the page (Ctrl+F5)
   - Clear browser cache
   - Disable any content blockers temporarily

## Device Management Issues

### Device Discovery Problems

**Issue**: Devices are not being discovered or appear offline.

**Troubleshooting Steps**:

1. **Verify Network Connectivity**
   - Ping the device from your workstation
   - Check if the device is reachable on the required ports
   - Verify firewall rules allow communication

2. **Check Credentials**
   - Verify device credentials are correct
   - Test credentials manually if possible
   - Check for any recent password changes

3. **Review Discovery Settings**
   - Verify the correct IP range is configured
   - Check the discovery schedule is active
   - Ensure the device type is supported by NetRaven

### Device Status Issues

**Issue**: Devices show incorrect status or intermittent connectivity.

**Troubleshooting Steps**:

1. **Verify Device Health**
   - Check if the device is truly online and operational
   - Verify interface status and CPU/memory utilization
   - Look for error messages on the device

2. **Check Monitoring Settings**
   - Verify monitoring interval is appropriate
   - Check timeout and retry settings
   - Review monitoring protocols (SNMP, API, etc.)

3. **Test Connectivity**
   - Use the **Test Connection** button for the device
   - Review the connection test results and errors
   - Check network path between NetRaven and the device

### Device Group Management

**Issue**: Problems with device grouping or filtering.

**Troubleshooting Steps**:

1. **Verify Group Configuration**
   - Check group membership criteria
   - Ensure dynamic group rules are correct
   - Verify that device attributes match group criteria

2. **Review User Permissions**
   - Confirm you have permission to view the device groups
   - Check role-based access settings
   - Verify device assignment to correct groups

3. **Refresh Group Data**
   - Use the **Refresh** button to update group data
   - Check if group recalculation is in progress
   - Verify that no group conflicts exist

## Configuration Management Issues

### Backup Failures

**Issue**: Configuration backups fail or contain errors.

**Troubleshooting Steps**:

1. **Check Device Connectivity**
   - Verify the device is online and reachable
   - Check credentials have sufficient privileges
   - Ensure correct protocol (SSH, SNMP, API) is enabled

2. **Review Backup Logs**
   - Navigate to **Backups** > **Backup History**
   - Find the failed backup and view details
   - Note specific error messages

3. **Manual Backup Test**
   - Try initiating a manual backup
   - Select different backup options
   - Check if specific configuration types fail

### Configuration Deployment Errors

**Issue**: Configuration deployments fail or cause device issues.

**Troubleshooting Steps**:

1. **Validate Configuration**
   - Use the **Validate** button before deployment
   - Check validation results for syntax errors
   - Verify configuration is appropriate for the device type

2. **Review Deployment Logs**
   - Navigate to **Deployments** > **Deployment History**
   - Check detailed logs for the failed deployment
   - Note any error messages or warnings

3. **Test with Smaller Changes**
   - Break down large configurations into smaller parts
   - Deploy incrementally to identify problematic sections
   - Use the test mode if available

### Configuration Comparison Issues

**Issue**: Configuration differences not showing correctly.

**Troubleshooting Steps**:

1. **Check Configuration Format**
   - Ensure configurations use consistent formatting
   - Verify device type matches the configuration format
   - Check for encoding or special character issues

2. **Adjust Comparison Settings**
   - Change the comparison view mode (side-by-side, inline)
   - Modify the diff settings to ignore whitespace or comments
   - Try comparing different versions

3. **Export and Manual Compare**
   - Export both configurations to files
   - Use an external diff tool to compare
   - Check for invisible characters or line ending differences

## Backup Management Issues

### Missing Backups

**Issue**: Expected backups are missing from the system.

**Troubleshooting Steps**:

1. **Check Backup Schedule**
   - Verify the backup schedule is active and correctly configured
   - Check if the device is included in scheduled backups
   - Review the last successful backup time

2. **Review Retention Policy**
   - Check the retention policy for automatic deletion
   - Verify backup storage limits haven't been reached
   - Look for cleanup tasks in the system logs

3. **Check Backup Location**
   - Verify the storage location is accessible
   - Check for storage permission issues
   - Confirm backup naming conventions haven't changed

### Backup Restoration Problems

**Issue**: Unable to restore a configuration from backup.

**Troubleshooting Steps**:

1. **Verify Backup Integrity**
   - Check if the backup file is valid and complete
   - Verify checksum or integrity markers if available
   - Try viewing the backup content before restoring

2. **Check Device Compatibility**
   - Ensure the device supports configuration restoration
   - Verify the device type matches the backup
   - Check device firmware version compatibility

3. **Review Restoration Options**
   - Try different restoration methods if available
   - Use partial restoration for specific sections
   - Check pre/post restoration commands

## Reporting Issues

### Report Generation Failures

**Issue**: Reports fail to generate or contain incorrect data.

**Troubleshooting Steps**:

1. **Check Report Parameters**
   - Verify time range and filter settings
   - Ensure selected devices are valid
   - Check for too broad queries that might time out

2. **Review Data Sources**
   - Verify data collection is working for included devices
   - Check if required metrics are being collected
   - Confirm data retention covers the report period

3. **Try Different Report Format**
   - Switch between report formats (PDF, CSV, HTML)
   - Try generating a simpler report
   - Check template customization for errors

### Scheduled Reports Not Delivered

**Issue**: Scheduled reports are not being delivered.

**Troubleshooting Steps**:

1. **Verify Schedule Settings**
   - Check the report schedule is active
   - Verify schedule timing and frequency
   - Ensure the report definition hasn't changed

2. **Check Notification Settings**
   - Verify email addresses are correct
   - Check if email notifications are properly configured
   - Look for email delivery errors in logs

3. **Test Manual Generation**
   - Try generating the report manually
   - Use the same parameters as the scheduled report
   - Check for errors in the manual generation process

## Dashboard Issues

### Widget Display Problems

**Issue**: Dashboard widgets show errors or no data.

**Troubleshooting Steps**:

1. **Refresh Widget Data**
   - Use the widget refresh button
   - Check data loading indicators
   - Verify if other widgets are affected

2. **Check Widget Configuration**
   - Review widget data source settings
   - Verify time range and filter settings
   - Check if data exists for the selected parameters

3. **Widget Permissions**
   - Ensure you have permissions to access all data sources
   - Check if device restrictions affect widget data
   - Verify role-based access for specific widgets

### Dashboard Performance Issues

**Issue**: Dashboards load slowly or cause browser performance problems.

**Troubleshooting Steps**:

1. **Reduce Dashboard Complexity**
   - Reduce the number of widgets on a single dashboard
   - Increase refresh intervals for real-time widgets
   - Split complex dashboards into multiple simpler ones

2. **Optimize Widget Settings**
   - Limit time ranges to necessary periods
   - Reduce the number of devices or metrics per widget
   - Use filtering to display only essential data

3. **Browser Performance**
   - Try a different browser
   - Close unused tabs and applications
   - Check system resource usage during dashboard loading

## Authentication and Access Issues

### Permission Denied Errors

**Issue**: You receive "Permission Denied" or "Access Forbidden" errors.

**Troubleshooting Steps**:

1. **Check User Role**
   - Verify your assigned role in NetRaven
   - Review specific permissions for your role
   - Check if role changes are needed

2. **Device Access Restrictions**
   - Confirm you have access to the specific devices
   - Check for device group restrictions
   - Review organization or tenant restrictions

3. **Feature Access**
   - Verify your license includes the feature
   - Check for module-specific permissions
   - Review feature enablement status

### Session Timeout Issues

**Issue**: You are frequently logged out or sessions expire quickly.

**Troubleshooting Steps**:

1. **Check Session Settings**
   - Review the configured session timeout
   - Ensure "Remember Me" is selected if available
   - Check for multiple sessions from the same account

2. **Browser Issues**
   - Verify cookies are enabled
   - Check for privacy settings blocking session storage
   - Disable incognito/private browsing mode

3. **Network Problems**
   - Check for network interruptions
   - Verify proxy settings don't interfere with sessions
   - Ensure stable connection to the NetRaven server

## Search Functionality Issues

### Search Results Problems

**Issue**: Search results are missing or irrelevant.

**Troubleshooting Steps**:

1. **Refine Search Terms**
   - Use more specific search terms
   - Try different keywords or phrases
   - Use advanced search operators if available

2. **Check Search Filters**
   - Verify appropriate filters are applied
   - Ensure date ranges are correct
   - Check category and type selections

3. **Verify Indexing Status**
   - Check if search indexing is complete
   - Verify recently added items are indexed
   - Allow time for new items to appear in search

## API and Integration Issues

### API Access Problems

**Issue**: Unable to access NetRaven API or receiving errors.

**Troubleshooting Steps**:

1. **Check API Credentials**
   - Verify API key or token is valid
   - Ensure credentials haven't expired
   - Confirm you have the correct endpoint URL

2. **Review API Permissions**
   - Check if your API key has the required permissions
   - Verify rate limits haven't been exceeded
   - Review API access logs for specific errors

3. **Test Basic Requests**
   - Use a simple GET request to test connectivity
   - Check the API documentation for correct syntax
   - Use tools like Postman to troubleshoot requests

### Integration Synchronization Issues

**Issue**: Problems with third-party system integration.

**Troubleshooting Steps**:

1. **Verify Connection Settings**
   - Check endpoint URLs and credentials
   - Ensure firewall rules allow communication
   - Verify TLS/SSL settings if applicable

2. **Review Sync Logs**
   - Check integration logs for error messages
   - Verify last successful synchronization time
   - Look for timeout or connection errors

3. **Test Manual Sync**
   - Try triggering a manual synchronization
   - Start with a limited scope to isolate issues
   - Check for specific item sync failures

## General Troubleshooting Tips

### Gathering Diagnostic Information

When reporting issues to administrators, gather the following information:

1. **Error Messages**
   - Exact error message text
   - Error codes or references
   - Screenshot of the error if possible

2. **Reproduction Steps**
   - Detailed steps to reproduce the issue
   - Specific devices, configurations, or reports affected
   - When the issue first occurred

3. **System Information**
   - Browser type and version
   - Operating system
   - Network environment (VPN, proxy, etc.)

### Checking System Status

Before troubleshooting, check overall system status:

1. Navigate to **Dashboard** > **System Status**
2. Check for any maintenance announcements
3. Verify all system components show normal status
4. Review recent system-wide notifications

### When to Contact Support

Escalate to your NetRaven administrator when:

1. You've tried the relevant troubleshooting steps without success
2. The issue affects multiple users or critical functionality
3. You encounter serious errors or data inconsistencies
4. You need permissions or configuration changes you can't make yourself

## Related Documentation

- [User Guide](./README.md)
- [Dashboard and Reporting Guide](./dashboard-reporting.md)
- [Configuration Management Guide](./configuration-management.md)
- [Administrator Troubleshooting Guide](../admin-guide/troubleshooting.md) 