"""
Services module initialization
Exports email service for easy importing
"""

from .email_service import EmailService
from .otp_service import OTPService

__all__ = ['EmailService', 'OTPService']