# NetRaven Job Tracking & Notifications

This document describes the job tracking and notification features implemented in NetRaven.

## Overview

The NetRaven job tracking and notification system provides comprehensive monitoring of scheduled jobs and real-time alerts for job completion and failures. It enables administrators and users to track the status and performance of their network automation jobs, receive notifications about job outcomes, and configure their notification preferences.

## Key Components

### Job Tracking Service

The Job Tracking Service (`job_tracking_service.py`) provides:

- Real-time tracking of job execution
- Detailed job status logging
- Automatic retry logic for failed jobs
- Performance statistics and metrics
- Integration with the notification system

API endpoints:
- `/job-logs/active` - Lists currently running jobs
- `/job-logs/statistics` - Provides job execution metrics and statistics

### Notification Service

The Notification Service (`notification_service.py`) handles:

- Email notifications for job completion/failure
- Templated notification messages with detailed job information
- User-configurable notification preferences
- Support for different notification channels (email, with future expansion for web, SMS, etc.)

### User Notification Preferences

Users can configure their notification preferences via:

- API endpoint: `/users/{user_id}/notification-preferences`
- Options include:
  - Enable/disable email notifications
  - Control notifications for job completion
  - Control notifications for job failures
  - Set notification frequency (immediate, hourly, daily)

## Database Schema Updates

- Added `notification_preferences` (JSONB) column to `users` table
- Added appropriate indexes for performance optimization
- Created migration script for database updates

## Usage Examples

### Checking Active Jobs

```bash
curl -H "Authorization: Bearer $TOKEN" http://api.netraven.local/job-logs/active
```

### Getting Job Statistics

```bash
curl -H "Authorization: Bearer $TOKEN" http://api.netraven.local/job-logs/statistics?time_period=week
```

### Updating Notification Preferences

```bash
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"email_notifications": true, "email_on_job_failure": true, "notification_frequency": "immediate"}' \
  http://api.netraven.local/users/me/notification-preferences
```

## Next Steps

- Implement UI components for job monitoring dashboard
- Add real-time WebSocket updates for job status changes
- Create UI for notification preference configuration
- Implement additional notification channels (Slack, SMS, etc.)
- Enhance metrics and reporting capabilities 