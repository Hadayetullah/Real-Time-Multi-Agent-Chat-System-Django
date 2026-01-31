"""
Email Service Module
Handles all email-related operations including OTP sending
Follows industry-standard separation of concerns pattern
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
import logging

# Initialize logger for tracking email operations
logger = logging.getLogger(__name__)


class EmailService:
    """
    Centralized email service for all email operations
    Makes email sending reusable and testable
    """
    
    @staticmethod
    def send_otp_email(email: str, otp: str, purpose: str = "signup") -> bool:
        """
        Send OTP verification email to user
        
        Args:
            email (str): Recipient email address
            otp (str): 6-digit OTP code
            purpose (str): Purpose of OTP (signup/login/reset)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Define subject based on purpose
            subject_map = {
                "signup": "Verify Your Agent Account - OTP",
                "login": "Login Verification Code - OTP",
                "reset": "Password Reset Code - OTP"
            }
            subject = subject_map.get(purpose, "Your Verification Code")
            
            # Create email body with OTP
            # In production, use HTML templates for better UX
            message = f"""
            Hello,
            
            Your verification code is: {otp}
            
            This code will expire in 5 minutes.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            Real-Time Chat Support Team
            """
            
            # For HTML email (production-ready approach)
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .otp-code {{ 
                        font-size: 32px; 
                        font-weight: bold; 
                        color: #4F46E5; 
                        text-align: center;
                        padding: 20px;
                        background: #F3F4F6;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .warning {{ color: #EF4444; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Email Verification</h2>
                    <p>Hello,</p>
                    <p>Your verification code is:</p>
                    <div class="otp-code">{otp}</div>
                    <p class="warning">This code will expire in 5 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>Real-Time Chat Support Team</p>
                </div>
            </body>
            </html>
            """
            
            # Send email using Django's email backend
            # Django will use settings.EMAIL_BACKEND configuration
            send_mail(
                subject=subject,
                message=strip_tags(message),  # Plain text fallback
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,  # HTML version
                fail_silently=False,  # Raise exception on failure in development
            )
            
            # Log successful email sending
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
        except Exception as e:
            # Log error for debugging
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False
    
    
    @staticmethod
    def send_welcome_email(email: str, username: str) -> bool:
        """
        Send welcome email after successful registration
        
        Args:
            email (str): User's email address
            username (str): User's display name
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            subject = "Welcome to Real-Time Chat System!"
            message = f"""
            Hello {username},
            
            Welcome to our Real-Time Multi-Agent Chat System!
            
            Your agent account has been successfully created.
            You can now log in and start assisting customers.
            
            Best regards,
            Support Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,  # Don't block registration if welcome email fails
            )
            
            logger.info(f"Welcome email sent to {email}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to send welcome email to {email}: {str(e)}")
            return False