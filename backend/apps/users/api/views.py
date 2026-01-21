import random

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import UserProfile
from apps.users.redis_client import redis_client
from .serializers import AgentSignupSerializer, AgentOTPVerifySerializer


class AgentSignupView(APIView):
    def post(self, request):
        serializer = AgentSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
            # User exists -> validate password
            if not user.check_password(password):
                return Response(
                    {"detail": "Invalid credentials"},
                    status=400
                )
        except User.DoesNotExist:
            # Create user properly (NO get_or_create while extending Built-in User model)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
            )

        otp = str(random.randint(100000, 999999))
        redis_client.setex(f"agent_otp:{email}", 300, otp)

        # In production, send OTP via email/SMS
        return Response(
            {"message": "OTP sent", "otp": otp},
            status=200
        )

    



class AgentOTPVerifyView(APIView):
    def post(self, request):
        serializer = AgentOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        key = f"agent_otp:{email}"
        stored_otp = redis_client.get(key)

        if not stored_otp or stored_otp != otp:
            return Response({"detail": "Invalid or expired OTP"}, status=400)

        user = User.objects.get(email=email)
        profile = user.profile
        profile.role = UserProfile.ROLE_AGENT
        profile.save()

        redis_client.delete(key)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })




class AgentLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials"}, status=401)

        if not user.check_password(password):
            return Response({"detail": "Invalid credentials"}, status=401)

        if user.profile.role != UserProfile.ROLE_AGENT:
            return Response({"detail": "User is not an agent"}, status=403)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })




# class AgentLoginView(APIView):
#     def post(self, request):
#         user = authenticate(
#             username=request.data.get("username"),
#             password=request.data.get("password")
#         )

#         if not user or user.profile.role != UserProfile.ROLE_AGENT:
#             return Response({"detail": "Invalid credentials"}, status=401)

#         refresh = RefreshToken.for_user(user)
#         return Response({
#             "access": str(refresh.access_token),
#             "refresh": str(refresh),
#         })




