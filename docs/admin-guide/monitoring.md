# Monitoring and Alerting Configuration

## Introduction

This guide explains how to configure and manage monitoring and alerting in NetRaven. Effective monitoring is essential for maintaining system health, identifying potential issues before they become critical, and ensuring optimal performance of your network management platform.

## Purpose

By following this guide, you will learn how to:
- Configure system health monitoring for NetRaven components
- Set up performance metrics collection and visualization
- Implement alerting for various system and network events
- Integrate NetRaven monitoring with external monitoring systems
- Customize monitoring dashboards and reports

## System Health Monitoring

### Component Health Checks

NetRaven provides built-in health checks for all major components:

1. **API Service Health**
   - Endpoint: `http://<server>:8000/api/health`
   - Monitors: API service status, database connectivity, background tasks
   - Status Codes: 200 (healthy), 503 (unhealthy)

2. **Device Gateway Health**
   - Endpoint: `http://<server>:8001/health`
   - Monitors: Gateway service status, device connectivity, protocol handlers
   - Status Codes: 200 (healthy), 503 (unhealthy)

3. **Scheduler Health**
   - Endpoint: `http://<server>:8002/health`
   - Monitors: Scheduler service status, task queue, job execution
   - Status Codes: 200 (healthy), 503 (unhealthy)

4. **Database Health**
   - Monitored via API service health check
   - Detailed metrics available through monitoring endpoints

### Configuring Health Check Frequency

To adjust health check frequency:

1. Edit the configuration file or set environment variables:
   ```yaml
   monitoring:
     health_check:
       interval_seconds: 60
       timeout_seconds: 10
       failure_threshold: 3
   ```

2. Restart the services to apply changes:
   ```bash
   docker-compose restart
   ```

### Health Check Dashboard

The health status of all components is visible on the System Health dashboard:

1. Navigate to **Dashboard** > **System Health**
2. View the Component Status widget for current health status
3. Check the Health History widget for historical health data

## Performance Metrics

### Available Metrics

NetRaven collects the following performance metrics:

1. **System Metrics**
   - CPU usage (per service)
   - Memory usage (per service)
   - Disk I/O and usage
   - Network I/O

2. **API Metrics**
   - Request count
   - Response times
   - Error rates
   - Endpoint usage

3. **Device Metrics**
   - Connection success rate
   - Command execution time
   - Data transfer rate
   - Connection concurrency

4. **Database Metrics**
   - Query execution time
   - Connection pool usage
   - Transaction rate
   - Table sizes

### Metrics Collection Configuration

To configure metrics collection:

1. Edit the configuration file or set environment variables:
   ```yaml
   monitoring:
     metrics:
       collection_interval: 15
       retention_days: 30
       detailed_logging: false
   ```

2. Restart the services to apply changes:
   ```bash
   docker-compose restart
   ```

### Metrics Endpoints

Metrics are available through the following endpoints:

1. **Prometheus Format**
   - API Service: `http://<server>:8000/metrics`
   - Gateway Service: `http://<server>:8001/metrics`
   - Scheduler Service: `http://<server>:8002/metrics`

2. **JSON Format**
   - API Service: `http://<server>:8000/api/metrics`
   - Gateway Service: `http://<server>:8001/api/metrics`
   - Scheduler Service: `http://<server>:8002/api/metrics`

## Alerting System

### Alert Types

NetRaven supports the following alert types:

1. **System Alerts**
   - Component down/unresponsive
   - Resource utilization (CPU, memory, disk)
   - Service degradation
   - Database issues

2. **Device Alerts**
   - Device unreachable
   - Authentication failures
   - Command execution failures
   - Configuration changes

3. **Backup Alerts**
   - Backup failures
   - Backup schedule missed
   - Storage capacity issues
   - Configuration integrity

4. **Security Alerts**
   - Authentication failures
   - Unauthorized access attempts
   - API rate limiting
   - Unusual activity patterns

### Configuring Alerts

To configure alerts:

1. Navigate to **Settings** > **Monitoring** > **Alert Configuration**
2. Click **Add Alert Rule**
3. Configure the alert rule:
   - **Name**: Descriptive name for the alert
   - **Type**: Select the alert type
   - **Conditions**: Define triggering conditions
   - **Severity**: Set alert priority (Info, Warning, Error, Critical)
   - **Notification**: Configure notification channels
4. Click **Save Rule**

#### Example Alert Rules

**High CPU Usage Alert**
```yaml
name: High CPU Usage
type: system
condition: cpu_usage > 80% for 5 minutes
severity: warning
notifications:
  - email: admin@example.com
  - slack: #netraven-alerts
```

**Device Unreachable Alert**
```yaml
name: Device Unreachable
type: device
condition: connection_failed > 3 times in 15 minutes
severity: error
notifications:
  - email: network-team@example.com
  - sms: +1234567890
```

### Alert Notification Channels

NetRaven supports multiple notification channels:

1. **Email Notifications**
   - Configure SMTP settings in **Settings** > **System** > **Email Configuration**
   - Define recipients and email templates

2. **Webhook Notifications**
   - Send alerts to external systems via HTTP webhooks
   - Configure endpoint URL and authentication

3. **Slack Integration**
   - Send alerts to Slack channels
   - Configure Slack webhook URL and channel

4. **SMS Notifications**
   - Send urgent alerts via SMS
   - Requires configuring SMS gateway settings

### Configuring Notification Channels

To set up notification channels:

1. Navigate to **Settings** > **Monitoring** > **Notification Channels**
2. Click **Add Channel**
3. Select the channel type
4. Configure the channel settings:
   - **Email**: SMTP server, port, credentials, from address
   - **Webhook**: URL, headers, authentication, payload format
   - **Slack**: Webhook URL, channel, bot name, icon
   - **SMS**: Gateway URL, credentials, message format
5. Test the channel by clicking **Test Notification**
6. Click **Save Channel**

## Log Management

### Log Sources

NetRaven generates logs from multiple sources:

1. **Application Logs**
   - API service logs
   - Gateway service logs
   - Scheduler service logs
   - Frontend logs

2. **System Logs**
   - Docker container logs
   - Host system logs
   - Database logs

3. **Audit Logs**
   - User activity logs
   - Authentication logs
   - Configuration changes
   - API access logs

### Log Locations

Logs are stored in the following locations:

**Docker Deployment**
```
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```

**Application Logs**
```
/app/logs/api.log
/app/logs/gateway.log
/app/logs/scheduler.log
/app/logs/auth.log
/app/logs/tasks.log
```

**Database Logs**
```
/var/lib/postgresql/data/log/
```

### Configuring Logging

To configure logging behavior:

1. Edit the configuration file or set environment variables:
   ```yaml
   logging:
     level: info                # debug, info, warning, error, critical
     format: json               # json or text
     retention_days: 30
     max_size_mb: 100
     backup_count: 10
   ```

2. Restart the services to apply changes:
   ```bash
   docker-compose restart
   ```

### Log Rotation

NetRaven automatically rotates logs based on size or time. To customize log rotation:

1. Edit the configuration file:
   ```yaml
   logging:
     rotation:
       max_size_mb: 100
       backup_count: 10
       compress: true
   ```

2. For Docker deployments, configure Docker's log rotation:
   ```json
   # /etc/docker/daemon.json
   {
     "log-driver": "json-file",
     "log-opts": {
       "max-size": "100m",
       "max-file": "10"
     }
   }
   ```

### Log Aggregation

For centralized logging, NetRaven supports integration with external log aggregation systems:

1. **Fluentd Integration**
   ```yaml
   logging:
     output: fluentd
     fluentd:
       host: fluentd-server
       port: 24224
       tag: netraven
   ```

2. **ELK Stack Integration**
   ```yaml
   logging:
     output: elasticsearch
     elasticsearch:
       hosts: ["http://elasticsearch:9200"]
       index: netraven-logs
       user: elastic
       password: changeme
   ```

## External Monitoring Integration

### Prometheus Integration

To integrate with Prometheus:

1. Configure Prometheus to scrape NetRaven metrics endpoints:
   ```yaml
   # prometheus.yml
   scrape_configs:
     - job_name: 'netraven'
       scrape_interval: 15s
       static_configs:
         - targets: ['netraven-api:8000', 'netraven-gateway:8001', 'netraven-scheduler:8002']
   ```

2. Ensure metrics endpoints are accessible to Prometheus

### Grafana Integration

To set up Grafana dashboards for NetRaven:

1. Add Prometheus as a data source in Grafana
2. Import the NetRaven dashboard templates:
   - Navigate to **Dashboards** > **Import**
   - Upload the dashboard JSON files from `monitoring/grafana-dashboards/`
   - Map the dashboard to your Prometheus data source

### SNMP Monitoring

To enable SNMP monitoring of NetRaven:

1. Configure SNMP agent settings:
   ```yaml
   monitoring:
     snmp:
       enabled: true
       community: public
       port: 161
       location: "Data Center 1"
       contact: "admin@example.com"
   ```

2. Restart the services to apply changes

3. Use your SNMP monitoring tool to poll NetRaven using the configured settings

## Custom Monitoring Dashboards

### Dashboard Templates

NetRaven provides the following monitoring dashboard templates:

1. **System Overview**
   - High-level system health and performance
   - Component status summary
   - Key performance indicators

2. **Detailed Performance**
   - In-depth performance metrics
   - Resource utilization trends
   - Service response times

3. **Alert Dashboard**
   - Active alerts
   - Alert history
   - Alert resolution status

### Creating Custom Dashboards

To create a custom monitoring dashboard:

1. Navigate to **Dashboard** > **System Monitoring**
2. Click **Create Dashboard**
3. Select dashboard layout and widgets
4. Configure each widget with desired metrics and visualization
5. Save and name your dashboard

### Exporting and Importing Dashboards

To share dashboards between NetRaven instances:

1. **Export Dashboard**
   - Navigate to the dashboard you want to export
   - Click **Actions** > **Export**
   - Save the JSON file

2. **Import Dashboard**
   - Navigate to **Dashboard** > **System Monitoring**
   - Click **Import Dashboard**
   - Upload the JSON file

## Best Practices

### Resource Monitoring Thresholds

Recommended threshold values for resource monitoring:

| Resource      | Warning Threshold | Critical Threshold |
|---------------|-------------------|-------------------|
| CPU Usage     | 70%              | 90%               |
| Memory Usage  | 80%              | 95%               |
| Disk Space    | 85%              | 95%               |
| Database Size | 80%              | 90%               |

### Monitoring Frequency

Recommended monitoring intervals:

| Metric Type       | Collection Interval |
|-------------------|---------------------|
| Health Checks     | 1-5 minutes         |
| System Metrics    | 15-30 seconds       |
| Device Status     | 5-15 minutes        |
| Log Collection    | Real-time           |
| Performance Stats | 1 minute            |

### Alert Configuration

Best practices for alert configuration:

1. **Define Severity Levels Clearly**
   - Critical: Requires immediate action
   - Error: Requires prompt attention
   - Warning: Potential issue, monitor closely
   - Info: Informational, no action required

2. **Avoid Alert Storms**
   - Use rate limiting for alerts
   - Group related alerts
   - Implement alert suppression during maintenance

3. **Establish Escalation Paths**
   - Define primary and secondary contacts
   - Set up escalation after defined periods
   - Document response procedures

## Troubleshooting

### Common Monitoring Issues

1. **High False Positive Rate**
   - Adjust alert thresholds
   - Implement trending analysis
   - Add validation conditions

2. **Missing Alerts**
   - Check notification channel configurations
   - Verify alert rules and conditions
   - Ensure services can reach notification endpoints

3. **Excessive Resource Usage by Monitoring**
   - Reduce collection frequency
   - Limit detailed metrics collection
   - Implement sampling for high-volume metrics

## Related Documentation

- [High Availability Setup](../deployment/high-availability.md)
- [Performance Optimization](./performance-optimization.md)
- [Backup and Recovery](./backup-recovery.md)
- [Security Configuration](./security.md) 