import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

from app.utils.logging_config import setup_logging
from app.utils.retry_handler import retry_with_backoff
from app.utils.circuit_breaker import circuit_breaker

logger = setup_logging("email-sender")

class EmailSender:
    """This class handles sending emails via SMTP."""
    
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str, smtp_from: str, use_tls: bool = True):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from = smtp_from
        self.use_tls = use_tls
    
    @retry_with_backoff(max_retries=3, base_delay=2.0, exceptions=(smtplib.SMTPException, ConnectionError))
    @circuit_breaker(failure_threshold=5, recovery_timeout=60, expected_exception=smtplib.SMTPException)
    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = True) -> bool:
        """
        Sends an email with retry and circuit breaker protection.
        
        Args:
            to_email: The recipient's email address.
            subject: The email subject.
            body: The email body (HTML or plain text).
            is_html: True if the body is HTML, False otherwise.
        
        Returns:
            True if the email was sent successfully.
        
        Raises:
            smtplib.SMTPException: If email sending fails.
        """
        try:
            # Creates message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_from
            message['To'] = to_email
            
            mime_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, mime_type))
            
            logger.info(f"Connecting to SMTP server {self.smtp_host}:{self.smtp_port}")
            
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=30)
            
            if self.smtp_user and self.smtp_password:
                server.login(self.smtp_user, self.smtp_password)
            
            # Send email
            server.send_message(message)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            raise
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipients refused: {str(e)}")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            raise smtplib.SMTPException(f"Failed to send email: {str(e)}")
