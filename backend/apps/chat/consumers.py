import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatSession, Message, TypingIndicator

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat
    Handles: messages, typing indicators, read receipts
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        # Get session ID from URL
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'chat_{self.session_id}'
        
        # Get user from scope (requires auth middleware)
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify user has access to this session
        has_access = await self.verify_session_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user joined notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Remove typing indicator
        await self.remove_typing_indicator()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Send user left notification
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': self.user.id,
                'username': self.user.username
            }
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read_receipt':
            await self.handle_read_receipt(data)
    
    async def handle_chat_message(self, data):
        """
        Handle incoming chat message
        """
        content = data.get('content')
        
        # Save message to database
        message = await self.save_message(content)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'message_id': str(message.message_id),
                    'content': message.content,
                    'sender_id': message.sender.id,
                    'sender_username': message.sender.username,
                    'created_at': message.created_at.isoformat(),
                    'message_type': message.message_type
                }
            }
        )
    
    async def handle_typing(self, data):
        """
        Handle typing indicator
        """
        is_typing = data.get('is_typing', False)
        
        if is_typing:
            await self.create_typing_indicator()
        else:
            await self.remove_typing_indicator()
        
        # Broadcast typing status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """
        Handle read receipt
        """
        message_id = data.get('message_id')
        await self.mark_message_as_read(message_id)
        
        # Broadcast read receipt
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'message_id': message_id,
                'user_id': self.user.id
            }
        )
    
    # WebSocket event handlers
    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send own typing indicator back
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id']
        }))
    
    async def user_joined(self, event):
        """Send user joined notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def user_left(self, event):
        """Send user left notification"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    # Database operations
    @database_sync_to_async
    def verify_session_access(self):
        """Verify user has access to session"""
        try:
            session = ChatSession.objects.get(session_id=self.session_id)
            return session.visitor == self.user or session.agent == self.user
        except ChatSession.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        session = ChatSession.objects.get(session_id=self.session_id)
        message = Message.objects.create(
            session=session,
            sender=self.user,
            content=content,
            message_type=Message.TYPE_TEXT
        )
        return message
    
    @database_sync_to_async
    def create_typing_indicator(self):
        """Create typing indicator"""
        session = ChatSession.objects.get(session_id=self.session_id)
        TypingIndicator.objects.get_or_create(
            session=session,
            user=self.user
        )
    
    @database_sync_to_async
    def remove_typing_indicator(self):
        """Remove typing indicator"""
        TypingIndicator.objects.filter(
            session__session_id=self.session_id,
            user=self.user
        ).delete()
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read"""
        try:
            message = Message.objects.get(message_id=message_id)
            if message.sender != self.user:
                message.mark_as_read()
        except Message.DoesNotExist:
            pass



