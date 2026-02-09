from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Count
from .models import ChatSession, Message, ChatSessionRating
from .serializers import (
    ChatSessionSerializer, MessageSerializer,
    ChatSessionCreateSerializer, MessageCreateSerializer,
    ChatSessionRatingSerializer
)


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for chat sessions
    Provides CRUD operations and custom actions
    """
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'session_id'
    
    def get_queryset(self):
        """
        Filter sessions based on user role
        Visitors see their own sessions
        Agents see assigned and waiting sessions
        """
        user = self.request.user
        
        # Check if user is agent
        if hasattr(user, 'profile') and user.profile.role == 'agent':
            # Agents see their sessions + waiting sessions
            return ChatSession.objects.filter(
                Q(agent=user) | Q(status=ChatSession.STATUS_WAITING)
            ).select_related('visitor', 'agent').prefetch_related('messages')
        else:
            # Visitors see only their own sessions
            return ChatSession.objects.filter(
                visitor=user
            ).select_related('agent').prefetch_related('messages')
    
    def create(self, request):
        """
        Create new chat session
        Automatically assigns visitor to current user
        """
        serializer = ChatSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create session with current user as visitor
        session = ChatSession.objects.create(
            visitor=request.user,
            **serializer.validated_data
        )
        
        # Create initial message if provided
        initial_message = request.data.get('initial_message')
        if initial_message:
            Message.objects.create(
                session=session,
                sender=request.user,
                content=initial_message,
                message_type=Message.TYPE_TEXT
            )
        
        return Response(
            ChatSessionSerializer(session, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def assign_to_me(self, request, session_id=None):
        """
        Assign waiting session to current agent
        """
        session = self.get_object()
        
        if session.status != ChatSession.STATUS_WAITING:
            return Response(
                {'error': 'Session is not waiting for agent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign agent and start session
        session.agent = request.user
        session.start_session()
        
        # Create system message
        Message.objects.create(
            session=session,
            sender=request.user,
            content=f"Agent {request.user.username} joined the chat",
            message_type=Message.TYPE_JOINED
        )
        
        return Response(ChatSessionSerializer(session).data)
    
    @action(detail=True, methods=['post'])
    def close_session(self, request, session_id=None):
        """
        Close chat session
        """
        session = self.get_object()
        session.close_session()
        
        # Create system message
        Message.objects.create(
            session=session,
            sender=request.user,
            content="Chat session has been closed",
            message_type=Message.TYPE_SYSTEM
        )
        
        return Response(ChatSessionSerializer(session).data)
    
    @action(detail=False, methods=['get'])
    def my_active_sessions(self, request):
        """
        Get user's active sessions
        """
        if hasattr(request.user, 'profile') and request.user.profile.role == 'agent':
            sessions = ChatSession.objects.filter(
                agent=request.user,
                status=ChatSession.STATUS_ACTIVE
            )
        else:
            sessions = ChatSession.objects.filter(
                visitor=request.user,
                status__in=[ChatSession.STATUS_WAITING, ChatSession.STATUS_ACTIVE]
            )
        
        serializer = ChatSessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def waiting_queue(self, request):
        """
        Get waiting sessions (agents only)
        """
        sessions = ChatSession.objects.filter(
            status=ChatSession.STATUS_WAITING
        ).order_by('-priority', 'created_at')
        
        serializer = ChatSessionSerializer(sessions, many=True, context={'request': request})
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for messages
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'message_id'
    
    def get_queryset(self):
        """
        Get messages for sessions user has access to
        """
        user = self.request.user
        
        # Get session_id from query params
        session_id = self.request.query_params.get('session_id')
        
        if session_id:
            # Filter messages for specific session
            return Message.objects.filter(
                session__session_id=session_id,
                is_deleted=False
            ).filter(
                Q(session__visitor=user) | Q(session__agent=user)
            ).select_related('sender', 'session')
        
        return Message.objects.none()
    
    def create(self, request):
        """
        Send a new message
        """
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        session_id = request.data.get('session_id')
        
        try:
            session = ChatSession.objects.get(session_id=session_id)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': 'Chat session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user is part of this session
        if session.visitor != request.user and session.agent != request.user:
            return Response(
                {'error': 'You are not part of this chat session'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create message
        message = Message.objects.create(
            session=session,
            sender=request.user,
            content=serializer.validated_data['content'],
            message_type=serializer.validated_data.get('message_type', Message.TYPE_TEXT),
            attachment=serializer.validated_data.get('attachment')
        )
        
        return Response(
            MessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, message_id=None):
        """
        Mark message as read
        """
        message = self.get_object()
        
        if message.sender == request.user:
            return Response(
                {'error': 'Cannot mark own message as read'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.mark_as_read()
        return Response(MessageSerializer(message).data)
    

