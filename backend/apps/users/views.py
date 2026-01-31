from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserProfile
from apps.services import OTPService, EmailService
from .serializers import AgentSignupSerializer, AgentOTPVerifySerializer


class AgentSignupView(APIView):
    """
    Agent Signup API View
    Handles agent registration with OTP verification
    Throttled to prevent abuse (30 requests per minute for anonymous users)
    """
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        """
        Handle POST request for agent signup
        Steps:
        1. Validate email and password
        2. Check if user exists, validate password if yes
        3. Create new user if doesn't exist
        4. Generate and send OTP via email
        """
        # Validate incoming data using serializer
        serializer = AgentSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            # Check if user already exists with this email
            user = User.objects.get(email=email)
            
            # User exists -> validate password
            # This allows existing users to re-register as agents
            if not user.check_password(password):
                return Response(
                    {"detail": "Invalid credentials"},
                    status=400
                )
        except User.DoesNotExist:
            # Create new user properly
            # Using create_user ensures password is hashed correctly
            user = User.objects.create_user(
                username=email,  # Using email as username for simplicity
                email=email,
                password=password,
            )

        # Generate OTP using OTPService
        otp = OTPService.generate_otp()
        
        # Store OTP in Redis with 5-minute expiration
        if not OTPService.store_otp(email, otp, purpose="signup"):
            return Response(
                {"detail": "Failed to generate OTP. Please try again."},
                status=500
            )
        
        # Send OTP via email using EmailService
        email_sent = EmailService.send_otp_email(email, otp, purpose="signup")
        
        if not email_sent:
            # Email sending failed, but OTP is stored
            # In production, you might want to log this and alert admins
            return Response(
                {"detail": "Failed to send OTP email. Please try again later."},
                status=500
            )

        # In development, return OTP in response for testing
        # In production, remove 'otp' from response for security
        response_data = {
            "message": "OTP sent to your email. Please verify to complete signup.",
            "email": email
        }
        
        # Only include OTP in development mode for testing
        # from django.conf import settings
        # if settings.DEBUG:
        #     response_data["otp"] = otp
        
        return Response(response_data, status=200)

    



class AgentOTPVerifyView(APIView):
    """
    Agent OTP Verification API View
    Verifies OTP and completes agent registration
    Issues JWT tokens upon successful verification
    """
    def post(self, request):
        """
        Handle POST request for OTP verification
        Steps:
        1. Validate email and OTP from request
        2. Verify OTP using OTPService
        3. Update user profile to agent role
        4. Generate JWT tokens
        5. Send welcome email (optional)
        """
        # Validate request data
        serializer = AgentOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        # Verify OTP using OTPService
        is_valid, message = OTPService.verify_otp(email, otp, purpose="signup")
        
        if not is_valid:
            # OTP verification failed
            return Response({"detail": message}, status=400)

        try:
            # Get user by email
            user = User.objects.get(email=email)
            
            # Get or create user profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': UserProfile.ROLE_AGENT}
            )
            
            # Update role to agent if profile already existed
            if not created and profile.role != UserProfile.ROLE_AGENT:
                profile.role = UserProfile.ROLE_AGENT
                profile.save()
            
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found. Please signup again."},
                status=404
            )

        # Generate JWT tokens for authentication
        # RefreshToken.for_user() creates both access and refresh tokens
        refresh = RefreshToken.for_user(user)
        
        # Send welcome email asynchronously (doesn't block response)
        # In production, use Celery for this
        EmailService.send_welcome_email(email, user.username)
        
        # Return tokens to client
        return Response({
            "message": "Agent account verified successfully",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "username": user.username,
                "role": profile.role
            }
        }, status=200)





class AgentLoginView(APIView):
    """
    Agent Login API View
    Authenticates agents and issues JWT tokens
    Throttled to prevent brute force attacks (120 requests per minute for authenticated users)
    """
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        """
        Handle POST request for agent login
        Steps:
        1. Validate email and password
        2. Check if user exists
        3. Verify password
        4. Verify user has agent role
        5. Generate JWT tokens
        """
        # Extract credentials from request
        email = request.data.get("email")
        password = request.data.get("password")

        # Validate required fields
        if not email or not password:
            return Response(
                {"detail": "Email and password are required"},
                status=400
            )

        try:
            # Find user by email
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether user exists (security best practice)
            return Response(
                {"detail": "Invalid credentials"},
                status=401
            )

        # Verify password using Django's built-in check_password
        # This method handles password hashing automatically
        if not user.check_password(password):
            return Response(
                {"detail": "Invalid credentials"},
                status=401
            )

        # Check if user has an agent profile
        try:
            profile = user.profile
            
            # Verify user is an agent
            if profile.role != UserProfile.ROLE_AGENT:
                return Response(
                    {"detail": "Access denied. Agent account required."},
                    status=403
                )
        except UserProfile.DoesNotExist:
            return Response(
                {"detail": "User profile not found. Please contact support."},
                status=403
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Return tokens and user info
        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "email": user.email,
                "username": user.username,
                "role": profile.role,
                "is_available": profile.is_available
            }
        }, status=200)





class ResendOTPView(APIView):
    """
    Resend OTP API View
    Allows users to request a new OTP if the previous one expired
    Throttled to prevent abuse
    """
    throttle_classes = [AnonRateThrottle]
    
    def post(self, request):
        """
        Handle POST request to resend OTP
        Generates new OTP and sends via email
        """
        # Get email from request
        email = request.data.get("email")
        purpose = request.data.get("purpose", "signup")  # Default to signup
        
        if not email:
            return Response(
                {"detail": "Email is required"},
                status=400
            )
        
        # Validate email format using serializer
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {"detail": "Invalid email format"},
                status=400
            )
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "No account found with this email"},
                status=404
            )
        
        # Generate and store new OTP
        new_otp = OTPService.resend_otp(email, purpose)
        
        if not new_otp:
            return Response(
                {"detail": "Failed to generate OTP. Please try again."},
                status=500
            )
        
        # Send OTP via email
        email_sent = EmailService.send_otp_email(email, new_otp, purpose)
        
        if not email_sent:
            return Response(
                {"detail": "Failed to send OTP email. Please try again later."},
                status=500
            )
        
        return Response({
            "message": "New OTP sent to your email",
            "email": email
        }, status=200)


