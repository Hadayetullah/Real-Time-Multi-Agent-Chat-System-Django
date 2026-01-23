import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.users.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
def test_agent_login_jwt():
    # Create user
    user = User.objects.create_user(
        username="agent_login@test.com",
        email="agent_login@test.com",
        password="StrongPass123",
    )

    # Mark user as agent (correct way)
    user.profile.role = UserProfile.ROLE_AGENT
    user.profile.save()

    client = APIClient()
    response = client.post(
        "/api/users/agent/login/",
        {
            "email": "agent_login@test.com",
            "password": "StrongPass123",
        },
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
