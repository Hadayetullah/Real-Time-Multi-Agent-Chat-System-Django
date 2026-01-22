import time
import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection

from apps.chat.models import ChatSession, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.last_message_ts = 0
        self.message_count = 0

        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]

        try:
            self.chat_session = await database_sync_to_async(
                ChatSession.objects.get
            )(id=self.chat_id)
        except ChatSession.DoesNotExist:
            raise DenyConnection("Chat session does not exist")

        if self.chat_session.status != ChatSession.STATUS_ACTIVE:
            raise DenyConnection("Chat session is closed")
    
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"chat_{self.session_id}"

        # Validate session exists
        exists = await self.session_exists()
        if not exists:
            await self.close()
            return

        # Identify user type
        user = self.scope.get("user")

        if user and user.is_authenticated:
            self.user = user
            self.user_type = "agent"
        else:
            # Anonymous visitor
            self.user = None
            self.user_type = "visitor"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        if self.chat_session.status != ChatSession.STATUS_ACTIVE:
            await self.send_json({
                "type": "error",
                "message": "Chat session is closed"
            })
            return

        data = json.loads(text_data)
        message_text = data.get("message")

        if not message_text:
            return
        
        now = time.time()

        # Allow max 5 messages per second
        if now - self.last_message_ts < 1:
            self.message_count += 1
        else:
            self.message_count = 1
            self.last_message_ts = now

        if self.message_count > 5:
            if self.message_count > 10:
                await self.close(code=4008) # Aggressive protection for abusive clients

            await self.send_json({
                "type": "error",
                "message": "Rate limit exceeded"
            })
            return

        message = await self.save_message(message_text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message.content,
                "sender": message.sender.username,
                "timestamp": message.created_at.isoformat(),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def session_exists(self):
        return ChatSession.objects.filter(id=self.session_id).exists()

    @database_sync_to_async
    def save_message(self, content):
        session = ChatSession.objects.get(id=self.session_id)

        if self.user_type == "agent":
            sender = self.user
        else:
            # Visitors do not have a User instance.
            sender = session.visitor  # visitor user created in Phase 2.

        return Message.objects.create(
            session=session,
            sender=sender,
            content=content,
        )



