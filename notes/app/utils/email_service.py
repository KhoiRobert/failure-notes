"""Email service for sending alerts via SMTP (Gmail)."""

import logging
import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


def send_email_alert(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> bool:
    """
    Send an email alert via SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body_html: HTML email body
        body_text: Plain text email body (optional, auto-generated from HTML if not provided)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not settings.EMAIL_ENABLED:
        logger.debug("Email alerts disabled; skipping email to %s", to_email)
        return False
    
    if not settings.EMAIL_SMTP_USER or not settings.EMAIL_SMTP_PASSWORD:
        logger.warning("Email SMTP credentials not configured; cannot send email")
        return False
    
    if not settings.EMAIL_FROM:
        logger.warning("EMAIL_FROM not configured; using SMTP_USER as from address")
        from_email = settings.EMAIL_SMTP_USER
    else:
        from_email = settings.EMAIL_FROM
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email
        
        # Add text and HTML parts
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
        
        # Send email via SMTP
        with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
            server.starttls()  # Enable TLS encryption
            server.login(settings.EMAIL_SMTP_USER, settings.EMAIL_SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info("Email alert sent successfully to %s: %s", to_email, subject)
        return True
    
    except Exception as e:
        logger.error("Failed to send email alert to %s: %s", to_email, e, exc_info=True)
        return False


def send_usage_alert_email(
    user_email: str,
    username: str,
    root_cause_title: str,
    root_cause_description: Optional[str],
    root_cause_solution: Optional[str],
    usage_count: int,
) -> bool:
    """
    Send an email alert when a user's root cause usage_count exceeds the threshold.
    
    Args:
        user_email: User's email address
        username: User's username
        root_cause_title: Title of the root cause
        root_cause_description: Description of the root cause (optional)
        root_cause_solution: Solution/recommendation for the root cause (optional)
        usage_count: Current usage count (times encountered)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    # Truncate title if too long to avoid email client subject line truncation
    # Most email clients handle up to 78 chars, but we'll use 60 to be safe
    max_title_length = 60
    truncated_title = (
        root_cause_title[:max_title_length] + "..."
        if len(root_cause_title) > max_title_length
        else root_cause_title
    )
    subject = f"⚠️ Alert: High Usage Count - {truncated_title}"
    
    # Format description and solution sections (escape HTML to prevent XSS)
    description_section = ""
    if root_cause_description:
        escaped_description = html.escape(root_cause_description)
        description_section = f"""
          <div style="margin: 15px 0;">
            <h4 style="margin-bottom: 8px; color: #555;">Description:</h4>
            <p style="margin: 0; color: #666; line-height: 1.6; white-space: pre-wrap;">{escaped_description}</p>
          </div>
        """
    
    solution_section = ""
    if root_cause_solution:
        escaped_solution = html.escape(root_cause_solution)
        solution_section = f"""
          <div style="margin: 15px 0; padding: 12px; background-color: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 4px;">
            <h4 style="margin-top: 0; margin-bottom: 8px; color: #2e7d32;">💡 Recommended Solution:</h4>
            <p style="margin: 0; color: #333; line-height: 1.6; white-space: pre-wrap;">{escaped_solution}</p>
          </div>
        """
    
    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #ff9800;">⚠️ Usage Alert</h2>
          <p>Hello <strong>{html.escape(username)}</strong>,</p>
          <p>You have exceeded the usage threshold for the following root cause:</p>
          
          <div style="background-color: #fff3e0; padding: 20px; border-left: 4px solid #ff9800; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #e65100;">{html.escape(root_cause_title)}</h3>
            
            {description_section}
            
            {solution_section}
            
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd;">
              <p style="margin: 8px 0;"><strong>Times Encountered:</strong> <span style="color: #d32f2f; font-size: 1.2em; font-weight: bold;">{usage_count}</span></p>
              <p style="margin: 8px 0;"><strong>Alert Threshold:</strong> {settings.EMAIL_ALERT_THRESHOLD}</p>
            </div>
          </div>
          
          <p style="color: #666;">This indicates you've encountered this root cause multiple times. Please review the recommended solution above and take preventive measures to avoid repeating this mistake.</p>
          
          <p style="margin-top: 30px; color: #999; font-size: 0.9em;">Best regards,<br>Failure Notes System</p>
        </div>
      </body>
    </html>
    """
    
    # Plain text version
    description_text = f"\nDescription: {root_cause_description}\n" if root_cause_description else ""
    solution_text = f"\n\nRecommended Solution:\n{root_cause_solution}\n" if root_cause_solution else ""
    
    body_text = f"""
Usage Alert

Hello {username},

You have exceeded the usage threshold for the following root cause:

Root Cause: {root_cause_title}
{description_text}{solution_text}
Times Encountered: {usage_count}
Alert Threshold: {settings.EMAIL_ALERT_THRESHOLD}

This indicates you've encountered this root cause multiple times. Please review the recommended solution above and take preventive measures to avoid repeating this mistake.

Best regards,
Failure Notes System
    """
    
    return send_email_alert(
        to_email=user_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
    )
