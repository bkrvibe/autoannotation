"""Email service using Postmark."""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Postmark email service for transactional emails."""
    
    def __init__(self):
        self.server_token = settings.POSTMARK_SERVER_TOKEN
        self.from_email = settings.EMAIL_FROM_ADDRESS
        self.from_name = settings.EMAIL_FROM_NAME
        self.frontend_url = settings.FRONTEND_URL
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Postmark client."""
        if self._client is None and self.server_token:
            try:
                from postmarker.core import PostmarkClient
                self._client = PostmarkClient(server_token=self.server_token)
            except ImportError:
                logger.warning("Postmark not installed. Run: pip install postmarker")
        return self._client
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via Postmark.
        
        Returns True if successful, False otherwise.
        """
        if not self.client:
            logger.warning(f"Email not sent (no client configured): {subject} -> {to_email}")
            # In development, log the email content for debugging
            logger.info(f"--- EMAIL PREVIEW ---")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Content:\n{text_content or html_content[:500]}...")
            logger.info(f"--- END EMAIL PREVIEW ---")
            return False
        
        try:
            response = self.client.emails.send(
                From=f"{self.from_name} <{self.from_email}>",
                To=to_email,
                Subject=subject,
                HtmlBody=html_content,
                TextBody=text_content,
                MessageStream="outbound"  # Use transactional stream
            )
            
            logger.info(f"Email sent successfully: {subject} -> {to_email} (MessageID: {response.get('MessageID')})")
            return True
                
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    def send_invite_email(
        self,
        to_email: str,
        tenant_name: str,
        invite_token: str,
        inviter_name: Optional[str] = None
    ) -> bool:
        """Send an invite email to a new user."""
        invite_url = f"{self.frontend_url}/invite?token={invite_token}"
        
        subject = "You're invited to CaliperAI Auto-Annotation"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .button:hover {{ background: #6d28d9; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CaliperAI Auto-Annotation</h1>
                </div>
                <div class="content">
                    <p>Hi there,</p>
                    <p>You've been invited to join <strong>{tenant_name}</strong> on CaliperAI Auto-Annotation.</p>
                    {"<p>Invited by: " + inviter_name + "</p>" if inviter_name else ""}
                    <p>Click the button below to activate your account:</p>
                    <p style="text-align: center;">
                        <a href="{invite_url}" class="button">Accept Invitation</a>
                    </p>
                    <p style="color: #6b7280; font-size: 14px;">This invitation link expires in 48 hours.</p>
                    <p style="color: #6b7280; font-size: 14px;">If the button doesn't work, copy and paste this URL into your browser:</p>
                    <p style="word-break: break-all; font-size: 12px; color: #9ca3af;">{invite_url}</p>
                </div>
                <div class="footer">
                    <p>CaliperAI · Enterprise Auto-Annotation</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
You're invited to CaliperAI Auto-Annotation

You've been invited to join {tenant_name} on CaliperAI Auto-Annotation.
{f"Invited by: {inviter_name}" if inviter_name else ""}

Click the link below to activate your account:
{invite_url}

This invitation link expires in 48 hours.

---
CaliperAI · Enterprise Auto-Annotation
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_magic_link_email(self, to_email: str, magic_token: str) -> bool:
        """Send a magic link for passwordless login."""
        magic_url = f"{self.frontend_url}/auth/magic?token={magic_token}"
        
        subject = "Your login link for CaliperAI Auto-Annotation"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
                .warning {{ background: #fef3c7; border: 1px solid #f59e0b; padding: 12px; border-radius: 6px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CaliperAI Auto-Annotation</h1>
                </div>
                <div class="content">
                    <p>Hi,</p>
                    <p>Click the button below to log in to your account:</p>
                    <p style="text-align: center;">
                        <a href="{magic_url}" class="button">Log In</a>
                    </p>
                    <div class="warning">
                        <strong>⚠️ This link expires in 15 minutes</strong> and can only be used once.
                    </div>
                    <p style="color: #6b7280; font-size: 14px;">If you didn't request this link, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>CaliperAI · Enterprise Auto-Annotation</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Your login link for CaliperAI Auto-Annotation

Click the link below to log in to your account:
{magic_url}

⚠️ This link expires in 15 minutes and can only be used once.

If you didn't request this link, you can safely ignore this email.

---
CaliperAI · Enterprise Auto-Annotation
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send a password reset email."""
        reset_url = f"{self.frontend_url}/auth/reset-password?token={reset_token}"
        
        subject = "Reset your CaliperAI password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #7c3aed, #8b5cf6); padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #7c3aed; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CaliperAI Auto-Annotation</h1>
                </div>
                <div class="content">
                    <p>Hi,</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </p>
                    <p style="color: #6b7280; font-size: 14px;">This link expires in 1 hour.</p>
                    <p style="color: #6b7280; font-size: 14px;">If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                </div>
                <div class="footer">
                    <p>CaliperAI · Enterprise Auto-Annotation</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Reset your CaliperAI password

We received a request to reset your password. Click the link below to create a new password:
{reset_url}

This link expires in 1 hour.

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.

---
CaliperAI · Enterprise Auto-Annotation
        """
        
        return self._send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
