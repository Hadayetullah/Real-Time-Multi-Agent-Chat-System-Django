"""
OTP Service Module
Handles OTP generation, storage, and validation
Implements secure OTP management with Redis caching
"""

import random
import string
from typing import Optional, Tuple
from apps.users.redis_client import redis_client
import logging

# Initialize logger
logger = logging.getLogger(__name__)


class OTPService:
    """
    OTP Management Service
    Centralized service for all OTP-related operations
    Uses Redis for temporary OTP storage with automatic expiration
    """
    
    # Configuration constants
    OTP_LENGTH = 6  # Standard 6-digit OTP
    OTP_EXPIRY_SECONDS = 300  # 5 minutes expiry time
    MAX_ATTEMPTS = 3  # Maximum verification attempts allowed
    
    @staticmethod
    def generate_otp(length: int = OTP_LENGTH) -> str:
        """
        Generate a random numeric OTP
        
        Args:
            length (int): Length of OTP to generate (default: 6)
            
        Returns:
            str: Generated OTP code
        """
        # Generate random digits for OTP
        otp = ''.join(random.choices(string.digits, k=length))
        logger.info(f"OTP generated with length {length}")
        return otp
    
    
    @staticmethod
    def store_otp(email: str, otp: str, purpose: str = "signup") -> bool:
        """
        Store OTP in Redis with expiration time
        
        Args:
            email (str): User's email address (used as key identifier)
            otp (str): Generated OTP code
            purpose (str): Purpose of OTP (signup/login/reset)
            
        Returns:
            bool: True if stored successfully
        """
        try:
            # Create unique Redis key for this OTP
            # Format: otp:{purpose}:{email}
            key = f"otp:{purpose}:{email}"
            
            # Store OTP with automatic expiration
            # Redis SETEX sets value and expiry in one atomic operation
            redis_client.setex(
                name=key,
                time=OTPService.OTP_EXPIRY_SECONDS,
                value=otp
            )
            
            # Initialize attempt counter
            # This tracks how many times user tried to verify this OTP
            attempts_key = f"{key}:attempts"
            redis_client.setex(
                name=attempts_key,
                time=OTPService.OTP_EXPIRY_SECONDS,
                value=0
            )
            
            logger.info(f"OTP stored for {email} with purpose {purpose}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store OTP for {email}: {str(e)}")
            return False
    
    
    @staticmethod
    def verify_otp(email: str, otp: str, purpose: str = "signup") -> Tuple[bool, str]:
        """
        Verify OTP code and check attempts
        
        Args:
            email (str): User's email address
            otp (str): OTP code to verify
            purpose (str): Purpose of OTP
            
        Returns:
            Tuple[bool, str]: (Success status, Error message if any)
        """
        try:
            # Construct Redis keys
            key = f"otp:{purpose}:{email}"
            attempts_key = f"{key}:attempts"
            
            # Retrieve stored OTP from Redis
            stored_otp = redis_client.get(key)
            
            # Check if OTP exists (not expired)
            if not stored_otp:
                logger.warning(f"OTP not found or expired for {email}")
                return False, "OTP has expired or does not exist"
            
            # Decode bytes to string if necessary
            if isinstance(stored_otp, bytes):
                stored_otp = stored_otp.decode('utf-8')
            
            # Get current attempt count
            attempts = redis_client.get(attempts_key)
            current_attempts = int(attempts.decode('utf-8') if isinstance(attempts, bytes) else attempts or 0)
            
            # Check if max attempts exceeded
            if current_attempts >= OTPService.MAX_ATTEMPTS:
                # Delete OTP to prevent further attempts
                redis_client.delete(key)
                redis_client.delete(attempts_key)
                logger.warning(f"Max OTP attempts exceeded for {email}")
                return False, "Maximum verification attempts exceeded. Please request a new OTP"
            
            # Verify OTP code
            if stored_otp == otp:
                # OTP is correct - delete it to prevent reuse
                redis_client.delete(key)
                redis_client.delete(attempts_key)
                logger.info(f"OTP verified successfully for {email}")
                return True, "OTP verified successfully"
            else:
                # Wrong OTP - increment attempt counter
                redis_client.incr(attempts_key)
                remaining_attempts = OTPService.MAX_ATTEMPTS - current_attempts - 1
                logger.warning(f"Invalid OTP attempt for {email}. Attempts remaining: {remaining_attempts}")
                return False, f"Invalid OTP. {remaining_attempts} attempts remaining"
                
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return False, "An error occurred during verification"
    
    
    @staticmethod
    def delete_otp(email: str, purpose: str = "signup") -> bool:
        """
        Delete OTP from Redis (useful for cancellation or cleanup)
        
        Args:
            email (str): User's email address
            purpose (str): Purpose of OTP
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            key = f"otp:{purpose}:{email}"
            attempts_key = f"{key}:attempts"
            
            # Delete both OTP and attempts counter
            redis_client.delete(key)
            redis_client.delete(attempts_key)
            
            logger.info(f"OTP deleted for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete OTP for {email}: {str(e)}")
            return False
    
    
    @staticmethod
    def resend_otp(email: str, purpose: str = "signup") -> Optional[str]:
        """
        Generate and store a new OTP (for resend functionality)
        Deletes old OTP first to ensure fresh attempt counter
        
        Args:
            email (str): User's email address
            purpose (str): Purpose of OTP
            
        Returns:
            Optional[str]: New OTP code if successful, None otherwise
        """
        try:
            # Delete old OTP first
            OTPService.delete_otp(email, purpose)
            
            # Generate new OTP
            new_otp = OTPService.generate_otp()
            
            # Store new OTP
            if OTPService.store_otp(email, new_otp, purpose):
                logger.info(f"OTP resent for {email}")
                return new_otp
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to resend OTP for {email}: {str(e)}")
            return None
        
        