# Dashboard and Reporting Guide

## Introduction

This guide explains how to use NetRaven's dashboard and reporting features to monitor network status, analyze device information, and generate custom reports. These tools provide valuable insights into your network infrastructure, helping you make informed decisions and maintain comprehensive documentation.

## Purpose

By following this guide, you will learn how to:
- Navigate and customize the NetRaven dashboard
- Understand the various dashboard widgets and their functions
- Generate standard and custom reports
- Schedule automated reports
- Export and share reports with stakeholders

## Dashboard Overview

### Accessing the Dashboard

The dashboard is the default landing page when you log into NetRaven. You can also access it any time by clicking **Dashboard** in the main navigation menu.

### Dashboard Layout

The NetRaven dashboard consists of the following elements:

1. **Header Bar**: Contains navigation menu, user profile, notifications, and search
2. **Dashboard Selector**: Switch between different dashboard views
3. **Time Range Selector**: Filter dashboard data by time period
4. **Widget Area**: Customizable space containing information widgets
5. **Status Bar**: Shows system health indicators and background task status

### Default Dashboards

NetRaven comes with several pre-configured dashboards:

- **Overview**: High-level summary of network status and recent activities
- **Device Status**: Focus on device health, connectivity, and performance
- **Backup Status**: Information about configuration backup status and history
- **Compliance**: Overview of compliance status and policy violations
- **System Health**: Metrics about the NetRaven system itself

## Dashboard Customization

### Creating a Custom Dashboard

To create a new dashboard:

1. Click the dashboard selector dropdown
2. Select **Create New Dashboard**
3. Enter a name and description for your dashboard
4. Choose a layout template (Grid, Column, or Free-form)
5. Click **Create**

### Adding Widgets

To add widgets to your dashboard:

1. On any dashboard view, click the **Edit** button
2. Click the **Add Widget** button
3. Browse the widget gallery or search for specific widgets
4. Click on a widget to see its description and preview
5. Click **Add to Dashboard** to place the widget
6. Drag and resize the widget as needed
7. Click **Save Dashboard** when finished

### Configuring Widgets

Each widget can be customized to show specific information:

1. Hover over a widget and click the **Settings** icon (gear)
2. Modify the widget settings:
   - **Title**: Custom widget name
   - **Refresh Rate**: How often the widget updates
   - **Size**: Widget dimensions
   - **Data Sources**: What information to display
   - **Visualization Options**: Charts, tables, or other display formats
3. Click **Apply** to update the widget

### Common Dashboard Widgets

#### Device Summary Widget
- Shows total device count by type, status, and vendor
- Configurable to show specific device groups
- Visual indicators for device status (Up, Down, Maintenance)

#### Recent Backups Widget
- Displays recent backup activities
- Shows success/failure statistics
- Allows direct access to backup details

#### Compliance Status Widget
- Shows overall compliance percentage
- Highlights policy violations
- Lists top non-compliant devices

#### Activity Timeline Widget
- Chronological view of system activities
- Filterable by activity type and users
- Interactive timeline with expandable details

## Reporting Features

### Report Types

NetRaven offers several types of reports:

- **Inventory Reports**: Device listings with detailed information
- **Configuration Reports**: Configuration analysis and comparison
- **Backup Reports**: Backup status and history
- **Compliance Reports**: Policy compliance status and violations
- **Activity Reports**: User and system activity logs
- **Custom Reports**: User-defined reports with custom data selection

### Generating Reports

To generate a report:

1. Navigate to **Reports** > **Generate Report**
2. Select the report type from the available options
3. Configure report parameters:
   - **Time Range**: Data collection period
   - **Devices**: Specific devices or device groups
   - **Data Fields**: Information to include
   - **Grouping**: How to organize the information
   - **Sorting**: Order of results
4. Click **Generate Report**
5. The report will be processed and displayed when complete

### Report Templates

To save report configurations for future use:

1. Configure a report as described above
2. Before generating, click **Save as Template**
3. Enter a name and description for the template
4. Choose visibility options (Private or Shared)
5. Click **Save Template**

To use a saved template:

1. Navigate to **Reports** > **Templates**
2. Select the template you want to use
3. Click **Generate Report**
4. Modify parameters if needed
5. Click **Generate Report**

### Scheduling Reports

To set up automatic report generation:

1. Navigate to **Reports** > **Scheduled Reports**
2. Click **Add Scheduled Report**
3. Configure the schedule:
   - **Report Template**: Select an existing template
   - **Schedule**: Define frequency (Daily, Weekly, Monthly)
   - **Delivery Method**: Email, File Export, or Dashboard
   - **Format**: PDF, CSV, Excel, or HTML
   - **Recipients**: Email addresses (if Email delivery selected)
4. Click **Save Schedule**

### Exporting Reports

Reports can be exported in various formats:

1. When viewing a report, click the **Export** button
2. Select the desired format:
   - **PDF**: Best for sharing and printing
   - **CSV**: Raw data for spreadsheet applications
   - **Excel**: Formatted spreadsheet
   - **HTML**: Web page format
3. Configure any format-specific options
4. Click **Export**
5. Save the file to your local system

### Report Subscriptions

To subscribe to regular report updates:

1. Navigate to **Reports** > **Subscriptions**
2. Click **Add Subscription**
3. Select the report template
4. Choose delivery frequency and format
5. Enter your email address
6. Click **Subscribe**

## Advanced Reporting

### Custom Data Queries

Advanced users can create custom data queries:

1. Navigate to **Reports** > **Custom Queries**
2. Click **New Query**
3. Write your SQL query in the editor
   ```sql
   SELECT d.hostname, d.device_type, COUNT(b.id) as backup_count
   FROM devices d
   LEFT JOIN backups b ON d.id = b.device_id
   WHERE b.created_at > '2023-01-01'
   GROUP BY d.hostname, d.device_type
   ORDER BY backup_count DESC
   ```
4. Click **Test Query** to validate
5. Once validated, click **Save Query**
6. Provide a name and description
7. Click **Save**

### Data Visualization Options

When creating reports, you can choose from various visualization types:

- **Tables**: Traditional row-column format
- **Bar Charts**: Compare values across categories
- **Line Charts**: Show trends over time
- **Pie Charts**: Display proportion relationships
- **Heat Maps**: Highlight patterns using color intensity
- **Network Diagrams**: Visual representation of network topology

### Report Permissions

To manage who can access specific reports:

1. Navigate to **Reports** > **Templates**
2. Select the report template
3. Click **Permissions**
4. Assign access levels to users or roles:
   - **View**: Can generate and view reports
   - **Edit**: Can modify the report template
   - **Admin**: Full control including deletion
5. Click **Save Permissions**

## Troubleshooting

### Common Issues

- **Slow Report Generation**: For large reports, try narrowing the scope or breaking into smaller reports
- **Missing Data**: Verify data sources and ensure collection processes are working
- **Widget Not Updating**: Check refresh settings and network connectivity
- **Export Failures**: Ensure you have sufficient permissions for the selected format

### Report Limitations

- Reports with extremely large datasets may be truncated
- Some visualization types have limits on data points
- Real-time data may have slight delays depending on collection intervals

## Related Documentation

- [User Management Guide](../admin-guide/user-management.md)
- [Device Management Guide](./device-management.md)
- [API Reference](../developer-guide/api-reference.md)
- [Custom Scripting](../developer-guide/custom-scripts.md) 