import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.chat.models import ChatSession, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"chat_{self.session_id}"

        self.user = self.scope.get("user", AnonymousUser())

        if not await self._is_authorized():
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")

        if not message:
            return

        msg = await self._save_message(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": msg.content,
                "sender": msg.sender.username,
                "timestamp": msg.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # Authorization & Persistence Helpers
    async def _is_authorized(self):
        try:
            session = await ChatSession.objects.aget(id=self.session_id)
        except ChatSession.DoesNotExist:
            return False

        if self.user.is_authenticated:
            return self.user in (session.agent, session.visitor)

        return False

    async def _save_message(self, content):
        return await Message.objects.acreate(
            session_id=self.session_id,
            sender=self.user,
            content=content
        )

