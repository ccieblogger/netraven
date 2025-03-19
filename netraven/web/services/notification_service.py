"""
Notification service for NetRaven.

This module provides services for sending notifications to users
about job completions and other system events.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, Any, Optional, List

from netraven.web.models.job_log import JobLog

# Configure logging
logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending notifications to users.
    
    This class provides methods for sending notifications via different
    channels like email, web notifications, etc.
    """
    
    def __init__(self):
        """Initialize the notification service with configuration values."""
        # SMTP configuration (from environment variables or defaults)
        self.smtp_server = os.environ.get("NETRAVEN_SMTP_SERVER", "localhost")
        self.smtp_port = int(os.environ.get("NETRAVEN_SMTP_PORT", "25"))
        self.smtp_username = os.environ.get("NETRAVEN_SMTP_USERNAME", "")
        self.smtp_password = os.environ.get("NETRAVEN_SMTP_PASSWORD", "")
        self.smtp_use_tls = os.environ.get("NETRAVEN_SMTP_USE_TLS", "false").lower() == "true"
        self.smtp_from_address = os.environ.get("NETRAVEN_SMTP_FROM_ADDRESS", "netraven@example.com")
        
        # Notification settings
        self.send_email_notifications = os.environ.get("NETRAVEN_SEND_EMAIL_NOTIFICATIONS", "true").lower() == "true"
        
        logger.info(f"Notification service initialized with SMTP server: {self.smtp_server}:{self.smtp_port}")
    
    def notify_job_completion(self, job_log: JobLog, user_email: str, device_name: str, user_preferences: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send a notification about a job completion.
        
        Args:
            job_log: The job log record
            user_email: Email address of the user to notify
            device_name: Name of the device the job ran on
            user_preferences: User's notification preferences
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Check user preferences
        if user_preferences is None:
            # Default preferences if not provided
            user_preferences = {
                "email_notifications": True,
                "email_on_job_completion": True,
                "email_on_job_failure": True,
                "notification_frequency": "immediate"
            }
        
        # Check if notifications are enabled for this user
        if not user_preferences.get("email_notifications", True):
            logger.info(f"Email notifications disabled for user with email {user_email}")
            return True  # Return success since this is the intended behavior
        
        # Check if this specific notification type is enabled
        is_success = job_log.status == "completed"
        if is_success and not user_preferences.get("email_on_job_completion", True):
            logger.info(f"Completion notifications disabled for user with email {user_email}")
            return True
        
        if not is_success and not user_preferences.get("email_on_job_failure", True):
            logger.info(f"Failure notifications disabled for user with email {user_email}")
            return True
        
        # Check notification frequency
        frequency = user_preferences.get("notification_frequency", "immediate")
        if frequency != "immediate":
            # For non-immediate frequencies, we'd queue the notification for later delivery
            # This would be implemented with a message queue system in a real application
            logger.info(f"Queuing notification for user with email {user_email} (frequency: {frequency})")
            return True
        
        # Create notification data
        subject = f"NetRaven Job {job_log.status.title()}: {job_log.job_type.title()} on {device_name}"
        
        # Format timestamp
        timestamp = job_log.end_time or datetime.utcnow()
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Format job data
        job_data = job_log.job_data or {}
        job_name = job_data.get("job_name", "Unnamed Job")
        
        # Format duration if available
        duration_str = ""
        if job_data and "duration_seconds" in job_data:
            duration = job_data["duration_seconds"]
            if duration < 60:
                duration_str = f"{duration:.1f} seconds"
            elif duration < 3600:
                duration_str = f"{duration / 60:.1f} minutes"
            else:
                duration_str = f"{duration / 3600:.1f} hours"
        
        # Create notification context
        context = {
            "job_id": job_log.id,
            "job_name": job_name,
            "job_type": job_log.job_type,
            "status": job_log.status,
            "device_name": device_name,
            "timestamp": timestamp_str,
            "result_message": job_log.result_message or "",
            "duration": duration_str,
            "is_success": job_log.status == "completed"
        }
        
        # Send notifications via enabled channels
        success = True
        
        # Send email notification if enabled
        if self.send_email_notifications:
            email_success = self._send_email_notification(user_email, subject, context)
            if not email_success:
                success = False
        
        # Additional notification channels could be added here (e.g., web push, SMS, etc.)
        
        return success
    
    def _send_email_notification(self, to_email: str, subject: str, context: Dict[str, Any]) -> bool:
        """
        Send an email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            context: Context data for email template
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.send_email_notifications:
            logger.debug("Email notifications are disabled")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from_address
            msg['To'] = to_email
            
            # Create plain text and HTML versions
            plain_text = self._format_plain_text_email(context)
            html_text = self._format_html_email(context)
            
            # Attach parts
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html_text, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            if self.smtp_username and self.smtp_password:
                # Use authenticated SMTP
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.smtp_use_tls:
                    smtp.starttls()
                smtp.login(self.smtp_username, self.smtp_password)
                smtp.send_message(msg)
                smtp.quit()
            else:
                # Use unauthenticated SMTP
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                smtp.send_message(msg)
                smtp.quit()
            
            logger.info(f"Sent email notification to {to_email} about job {context['job_id']}")
            return True
        except Exception as e:
            logger.exception(f"Error sending email notification: {str(e)}")
            return False
    
    def _format_plain_text_email(self, context: Dict[str, Any]) -> str:
        """
        Format plain text email content.
        
        Args:
            context: Context data for email template
            
        Returns:
            str: Formatted plain text email content
        """
        status_emoji = "✅" if context["is_success"] else "❌"
        
        text = f"""
NetRaven Job Notification {status_emoji}

Job: {context['job_name']}
Type: {context['job_type']}
Status: {context['status'].title()}
Device: {context['device_name']}
Time: {context['timestamp']}
"""

        if context['duration']:
            text += f"Duration: {context['duration']}\n"
            
        if context['result_message']:
            text += f"\nResult: {context['result_message']}\n"
            
        text += """
---
This is an automated message from NetRaven.
"""
        return text
    
    def _format_html_email(self, context: Dict[str, Any]) -> str:
        """
        Format HTML email content.
        
        Args:
            context: Context data for email template
            
        Returns:
            str: Formatted HTML email content
        """
        status_color = "#28a745" if context["is_success"] else "#dc3545"
        status_text = "Completed Successfully" if context["is_success"] else "Failed"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #0056b3; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        .status {{ font-weight: bold; color: {status_color}; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>NetRaven Job Notification</h2>
        </div>
        <div class="content">
            <p>Your scheduled job has completed with the following status:</p>
            
            <table>
                <tr>
                    <th>Job Name:</th>
                    <td>{context['job_name']}</td>
                </tr>
                <tr>
                    <th>Job Type:</th>
                    <td>{context['job_type'].title()}</td>
                </tr>
                <tr>
                    <th>Status:</th>
                    <td class="status">{status_text}</td>
                </tr>
                <tr>
                    <th>Device:</th>
                    <td>{context['device_name']}</td>
                </tr>
                <tr>
                    <th>Completion Time:</th>
                    <td>{context['timestamp']}</td>
                </tr>
"""

        if context['duration']:
            html += f"""
                <tr>
                    <th>Duration:</th>
                    <td>{context['duration']}</td>
                </tr>
"""
            
        html += """
            </table>
"""

        if context['result_message']:
            html += f"""
            <h3>Result Message:</h3>
            <p>{context['result_message']}</p>
"""
            
        html += """
        </div>
        <div class="footer">
            <p>This is an automated message from NetRaven. Please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

# Singleton instance
_notification_service = None

def get_notification_service() -> NotificationService:
    """
    Get the notification service singleton instance.
    
    Returns:
        NotificationService: Notification service instance
    """
    global _notification_service
    
    if _notification_service is None:
        _notification_service = NotificationService()
    
    return _notification_service 