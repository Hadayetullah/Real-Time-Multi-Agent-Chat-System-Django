import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.users.models import UserProfile
from apps.users.redis_client import redis_client

User = get_user_model()


@pytest.mark.django_db
def test_agent_signup_and_otp_verification():
    client = APIClient()
    email = "agent_test@test.com"
    password = "StrongPass123"

    # ---- Signup ----
    signup_response = client.post(
        "/api/users/agent/signup/",
        {
            "email": email,
            "password": password,
        },
        format="json",
    )

    assert signup_response.status_code == 200
    assert "otp" in signup_response.data

    otp = signup_response.data["otp"]

    # OTP must exist in Redis
    redis_key = f"agent_otp:{email}"
    assert redis_client.get(redis_key) == otp

    # ---- Verify OTP ----
    verify_response = client.post(
        "/api/users/agent/verify-otp/",
        {
            "email": email,
            "otp": otp,
        },
        format="json",
    )

    assert verify_response.status_code == 200
    assert "access" in verify_response.data
    assert "refresh" in verify_response.data

    # ---- Verify DB state ----
    user = User.objects.get(email=email)
    user.profile.refresh_from_db()

    assert user.profile.role == UserProfile.ROLE_AGENT

    # OTP must be deleted after verification
    assert redis_client.get(redis_key) is None









# import pytest
# from django.contrib.auth.models import User
# from rest_framework.test import APIClient

# @pytest.mark.django_db
# def test_agent_signup_and_otp_verification():
#     client = APIClient()

#     signup_response = client.post(
#         "/api/users/agent/signup/",
#         {
#             "email": "agent_test@test.com",
#             "password": "StrongPass123"
#         },
#         format="json"
#     )

#     assert signup_response.status_code == 201

#     user = User.objects.get(email="agent_test@test.com")

#     # OTP should exist
#     assert user.profile.otp_code is not None

#     verify_response = client.post(
#         "/api/users/agent/verify-otp/",
#         {
#             "email": "agent_test@test.com",
#             "otp": user.profile.otp_code
#         },
#         format="json"
#     )

#     assert verify_response.status_code == 200
#     user.refresh_from_db()
#     assert user.profile.is_agent is True
