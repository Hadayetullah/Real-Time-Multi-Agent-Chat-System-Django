import pytest
from django.contrib.auth import get_user_model

from apps.chat.models import ChatSession, Message

User = get_user_model()


@pytest.mark.django_db
def test_message_saved_to_database():
    visitor = User.objects.create_user(
        username="visitor@test.com",
        password="StrongPass123",
    )

    agent = User.objects.create_user(
        username="agent@test.com",
        password="StrongPass123",
    )

    session = ChatSession.objects.create(
        visitor=visitor,
        agent=agent,
    )

    Message.objects.create(
        session=session,
        sender=agent,
        content="Hello from test",
    )

    msg = Message.objects.get(session=session)
    assert msg.content == "Hello from test"
    assert msg.sender == agent

    assert Message.objects.filter(session=session).count() == 1



