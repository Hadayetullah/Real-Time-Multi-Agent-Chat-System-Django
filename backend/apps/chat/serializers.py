"""
Chat Serializers Module
Provides serialization for chat models to/from JSON
Handles validation and nested relationships
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatSession, Message, TypingIndicator, ChatSessionRating

# Get the User model
User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user information for chat display
    Only includes safe, public information
    """
    
    # Full name derived from username or email
    full_name = serializers.SerializerMethodField()
    
    # Online status (will be populated from Redis or WebSocket status)
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'is_online']
        read_only_fields = ['id', 'username', 'email']
    
    def get_full_name(self, obj):
        """
        Get user's full name or fallback to username
        """
        if hasattr(obj, 'first_name') and hasattr(obj, 'last_name'):
            full_name = f"{obj.first_name} {obj.last_name}".strip()
            return full_name if full_name else obj.username
        return obj.username
    
    def get_is_online(self, obj):
        """
        Check if user is currently online
        This would typically check Redis or WebSocket connections
        """
        # Placeholder - implement with Redis in production
        return False


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for chat messages
    Handles message creation, updates, and retrieval
    """
    
    # Nested sender information
    sender = UserBasicSerializer(read_only=True)
    
    # Sender ID for message creation
    sender_id = serializers.IntegerField(write_only=True, required=False)
    
    # Session ID for message creation
    session_id = serializers.UUIDField(write_only=True, required=False)
    
    # Read-only fields for display
    attachment_url = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'message_id', 'session_id', 'sender', 'sender_id',
            'message_type', 'content', 'attachment', 'attachment_url',
            'attachment_name', 'attachment_size', 'status', 'is_read',
            'read_at', 'created_at', 'updated_at', 'is_deleted',
            'time_ago'
        ]
        read_only_fields = [
            'message_id', 'created_at', 'updated_at', 'is_deleted',
            'read_at', 'attachment_url', 'time_ago'
        ]
    
    def get_attachment_url(self, obj):
        """
        Get full URL for attachment if present
        """
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
            return obj.attachment.url
        return None
    
    def get_time_ago(self, obj):
        """
        Get human-readable time ago string
        """
        from django.utils.timesince import timesince
        return timesince(obj.created_at)
    
    def create(self, validated_data):
        """
        Create a new message
        """
        # Get session from session_id UUID
        session_id = validated_data.pop('session_id', None)
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except ChatSession.DoesNotExist:
                raise serializers.ValidationError("Chat session not found")
        
        # Get sender from sender_id
        sender_id = validated_data.pop('sender_id', None)
        if sender_id:
            try:
                sender = User.objects.get(id=sender_id)
                validated_data['sender'] = sender
            except User.DoesNotExist:
                raise serializers.ValidationError("Sender not found")
        
        # Create message
        message = Message.objects.create(**validated_data)
        
        # Increment session message count
        message.session.increment_message_count()
        
        return message


class MessageCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating messages via API
    """
    
    content = serializers.CharField(required=True)
    message_type = serializers.ChoiceField(
        choices=Message.TYPE_CHOICES,
        default=Message.TYPE_TEXT
    )
    attachment = serializers.FileField(required=False, allow_null=True)
    
    def validate_content(self, value):
        """
        Validate message content is not empty
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for chat sessions
    Handles session creation, updates, and retrieval
    """
    
    # Nested user information
    visitor = UserBasicSerializer(read_only=True)
    agent = UserBasicSerializer(read_only=True)
    previous_agent = UserBasicSerializer(read_only=True)
    
    # User IDs for creation
    visitor_id = serializers.IntegerField(write_only=True, required=False)
    agent_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Latest messages (optional, controlled by query param)
    latest_messages = serializers.SerializerMethodField()
    
    # Unread message count
    unread_count = serializers.SerializerMethodField()
    
    # Time calculations
    wait_time_display = serializers.SerializerMethodField()
    duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id', 'visitor', 'visitor_id', 'agent', 'agent_id',
            'previous_agent', 'status', 'priority', 'subject', 'department',
            'tags', 'visitor_name', 'visitor_email', 'visitor_phone',
            'visitor_ip', 'visitor_user_agent', 'visitor_location',
            'referrer_url', 'current_page', 'internal_notes',
            'created_at', 'started_at', 'closed_at', 'last_message_at',
            'wait_time_seconds', 'wait_time_display', 'duration_seconds',
            'duration_display', 'rating', 'feedback', 'message_count',
            'latest_messages', 'unread_count'
        ]
        read_only_fields = [
            'session_id', 'created_at', 'started_at', 'closed_at',
            'last_message_at', 'wait_time_seconds', 'duration_seconds',
            'message_count', 'latest_messages', 'unread_count',
            'wait_time_display', 'duration_display'
        ]
    
    def get_latest_messages(self, obj):
        """
        Get latest N messages for this session
        Only include if 'include_messages' query param is True
        """
        request = self.context.get('request')
        if request and request.query_params.get('include_messages') == 'true':
            # Get last 50 messages
            messages = obj.messages.filter(is_deleted=False).order_by('-created_at')[:50]
            return MessageSerializer(messages, many=True, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        """
        Get count of unread messages
        Count depends on current user's role
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Count messages not sent by current user and not read
            return obj.messages.filter(
                is_read=False,
                is_deleted=False
            ).exclude(sender=request.user).count()
        return 0
    
    def get_wait_time_display(self, obj):
        """
        Convert wait time seconds to human-readable format
        """
        if obj.wait_time_seconds:
            minutes, seconds = divmod(obj.wait_time_seconds, 60)
            if minutes > 0:
                return f"{minutes}m {seconds}s"
            return f"{seconds}s"
        return "N/A"
    
    def get_duration_display(self, obj):
        """
        Convert duration seconds to human-readable format
        """
        if obj.duration_seconds:
            hours, remainder = divmod(obj.duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m {seconds}s"
        return "N/A"


class ChatSessionCreateSerializer(serializers.Serializer):
    """
    Simplified serializer for creating chat sessions
    """
    
    subject = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=ChatSession.PRIORITY_CHOICES,
        default=ChatSession.PRIORITY_NORMAL
    )
    visitor_name = serializers.CharField(required=False, allow_blank=True)
    visitor_email = serializers.EmailField(required=False, allow_blank=True)
    visitor_phone = serializers.CharField(required=False, allow_blank=True)
    referrer_url = serializers.URLField(required=False, allow_blank=True)
    current_page = serializers.URLField(required=False, allow_blank=True)
    initial_message = serializers.CharField(required=False, allow_blank=True)


class ChatSessionRatingSerializer(serializers.ModelSerializer):
    """
    Serializer for session ratings
    """
    
    session_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = ChatSessionRating
        fields = [
            'session', 'session_id', 'overall_rating',
            'agent_friendliness', 'response_time', 'problem_resolution',
            'feedback', 'would_recommend', 'created_at'
        ]
        read_only_fields = ['session', 'created_at']
    
    def validate_overall_rating(self, value):
        """
        Validate rating is between 1 and 5
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        """
        Create rating for a session
        """
        session_id = validated_data.pop('session_id', None)
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except ChatSession.DoesNotExist:
                raise serializers.ValidationError("Chat session not found")
        
        # Also update the rating fields in ChatSession model
        if 'session' in validated_data:
            session = validated_data['session']
            session.add_rating(
                validated_data.get('overall_rating'),
                validated_data.get('feedback', '')
            )
        
        return ChatSessionRating.objects.create(**validated_data)


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """
    Serializer for typing indicators
    """
    
    user = UserBasicSerializer(read_only=True)
    session_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = TypingIndicator
        fields = ['session', 'session_id', 'user', 'created_at']
        read_only_fields = ['created_at']


class ChatStatisticsSerializer(serializers.Serializer):
    """
    Serializer for chat statistics
    Used for dashboard analytics
    """
    
    total_sessions = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    waiting_sessions = serializers.IntegerField()
    closed_sessions = serializers.IntegerField()
    average_wait_time = serializers.FloatField()
    average_duration = serializers.FloatField()
    average_rating = serializers.FloatField()
    total_messages = serializers.IntegerField()
    sessions_today = serializers.IntegerField()


    