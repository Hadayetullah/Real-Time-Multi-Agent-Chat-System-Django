from django.utils import timezone
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator
import uuid

###############################################################################
# Professional Chat System Models
# This module contains all models for a production-ready chat system
###############################################################################


class ChatSession(models.Model):
    """
    Represents a chat session between a visitor and an agent
    
    A chat session is created when a visitor initiates a chat request.
    It can be assigned to an available agent and tracks the entire
    conversation lifecycle from initiation to closure.
    """
    
    # Session status choices
    STATUS_WAITING = "waiting"          # Waiting for agent assignment
    STATUS_ACTIVE = "active"            # Actively chatting
    STATUS_CLOSED = "closed"            # Session ended
    STATUS_TRANSFERRED = "transferred"  # Transferred to another agent
    STATUS_ABANDONED = "abandoned"      # Visitor left before assignment
    
    STATUS_CHOICES = (
        (STATUS_WAITING, "Waiting for Agent"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_TRANSFERRED, "Transferred"),
        (STATUS_ABANDONED, "Abandoned"),
    )
    
    # Priority levels for queue management
    PRIORITY_LOW = 1
    PRIORITY_NORMAL = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4
    
    PRIORITY_CHOICES = (
        (PRIORITY_LOW, "Low"),
        (PRIORITY_NORMAL, "Normal"),
        (PRIORITY_HIGH, "High"),
        (PRIORITY_URGENT, "Urgent"),
    )
    
    # Unique session identifier (UUID for security and uniqueness)
    session_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,  # Index for faster lookups
        help_text="Unique identifier for this chat session"
    )
    
    # Visitor who initiated the chat
    visitor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="visitor_sessions",
        help_text="Visitor who initiated this chat"
    )
    
    # Agent assigned to this session (can be null if waiting)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_sessions",
        help_text="Agent handling this chat session"
    )
    
    # Previous agent (in case of transfer)
    previous_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_agent_sessions",
        help_text="Previous agent before transfer"
    )
    
    # Session status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_WAITING,
        db_index=True,  # Index for faster status-based queries
        help_text="Current status of the chat session"
    )
    
    # Priority level (for queue management)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=PRIORITY_NORMAL,
        db_index=True,
        help_text="Priority level for queue ordering"
    )
    
    # Subject/Title of the chat (optional)
    subject = models.CharField(
        max_length=200,
        blank=True,
        help_text="Subject or title of the chat conversation"
    )
    
    # Department/Category (for routing to specialized agents)
    department = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Department or category for this chat"
    )
    
    # Tags for organization and searching
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated tags for this session"
    )
    
    # Visitor information (captured at session start)
    visitor_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Visitor's display name"
    )
    visitor_email = models.EmailField(
        blank=True,
        help_text="Visitor's email address"
    )
    visitor_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Visitor's phone number"
    )
    
    # Technical information
    visitor_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Visitor's IP address"
    )
    visitor_user_agent = models.TextField(
        blank=True,
        help_text="Visitor's browser user agent"
    )
    visitor_location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Visitor's geographic location"
    )
    
    # Referral information
    referrer_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL where visitor came from"
    )
    current_page = models.URLField(
        max_length=500,
        blank=True,
        help_text="Page where chat was initiated"
    )
    
    # Notes and internal comments (only visible to agents)
    internal_notes = models.TextField(
        blank=True,
        help_text="Internal notes for agents (not visible to visitor)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,  # Index for time-based queries
        help_text="When the chat session was created"
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When agent joined and chat started"
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the chat session was closed"
    )
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last message in this session"
    )
    
    # Wait time tracking
    wait_time_seconds = models.IntegerField(
        default=0,
        help_text="How long visitor waited before agent joined (in seconds)"
    )
    
    # Session duration tracking
    duration_seconds = models.IntegerField(
        default=0,
        help_text="Total duration of active chat (in seconds)"
    )
    
    # Rating and feedback
    rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="Visitor's rating (1-5 stars)"
    )
    feedback = models.TextField(
        blank=True,
        help_text="Visitor's feedback/comment"
    )
    
    # Message count (denormalized for performance)
    message_count = models.IntegerField(
        default=0,
        help_text="Total number of messages in this session"
    )
    
    class Meta:
        ordering = ['-created_at']  # Most recent first
        indexes = [
            # Composite indexes for common queries
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['visitor', 'created_at']),
        ]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"
    
    def __str__(self):
        return f"Session {self.session_id} - {self.get_status_display()}"
    
    def start_session(self):
        """
        Mark session as started when agent joins
        Calculates wait time
        """
        if self.status == self.STATUS_WAITING:
            self.status = self.STATUS_ACTIVE
            self.started_at = timezone.now()
            # Calculate wait time
            self.wait_time_seconds = int((self.started_at - self.created_at).total_seconds())
            self.save(update_fields=['status', 'started_at', 'wait_time_seconds'])
    
    def close_session(self, reason=None):
        """
        Close the chat session
        Calculates total duration
        """
        if self.status not in [self.STATUS_CLOSED, self.STATUS_ABANDONED]:
            self.status = self.STATUS_CLOSED
            self.closed_at = timezone.now()
            # Calculate duration if session was active
            if self.started_at:
                self.duration_seconds = int((self.closed_at - self.started_at).total_seconds())
            self.save(update_fields=['status', 'closed_at', 'duration_seconds'])
    
    def transfer_to_agent(self, new_agent):
        """
        Transfer chat session to another agent
        """
        self.previous_agent = self.agent
        self.agent = new_agent
        self.status = self.STATUS_TRANSFERRED
        self.save(update_fields=['previous_agent', 'agent', 'status'])
    
    def add_rating(self, rating, feedback=''):
        """
        Add visitor rating and feedback
        """
        self.rating = rating
        self.feedback = feedback
        self.save(update_fields=['rating', 'feedback'])
    
    def increment_message_count(self):
        """
        Increment message counter (called when new message is created)
        """
        self.message_count += 1
        self.last_message_at = timezone.now()
        self.save(update_fields=['message_count', 'last_message_at'])


class Message(models.Model):
    """
    Represents a single message in a chat session
    
    Messages can be sent by visitors, agents, or the system.
    Supports different message types including text, files, and system messages.
    """
    
    # Message types
    TYPE_TEXT = "text"              # Regular text message
    TYPE_FILE = "file"              # File attachment
    TYPE_IMAGE = "image"            # Image attachment
    TYPE_SYSTEM = "system"          # System-generated message
    TYPE_TRANSFER = "transfer"      # Agent transfer notification
    TYPE_JOINED = "joined"          # Agent joined notification
    TYPE_LEFT = "left"              # Agent/visitor left notification
    
    TYPE_CHOICES = (
        (TYPE_TEXT, "Text"),
        (TYPE_FILE, "File"),
        (TYPE_IMAGE, "Image"),
        (TYPE_SYSTEM, "System"),
        (TYPE_TRANSFER, "Transfer"),
        (TYPE_JOINED, "Joined"),
        (TYPE_LEFT, "Left"),
    )
    
    # Delivery status choices
    STATUS_SENT = "sent"            # Message sent
    STATUS_DELIVERED = "delivered"  # Message delivered to recipient
    STATUS_READ = "read"            # Message read by recipient
    STATUS_FAILED = "failed"        # Message failed to send
    
    STATUS_CHOICES = (
        (STATUS_SENT, "Sent"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_READ, "Read"),
        (STATUS_FAILED, "Failed"),
    )
    
    # Unique message identifier
    message_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Unique identifier for this message"
    )
    
    # Chat session this message belongs to
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        db_index=True,  # Index for session-based queries
        help_text="Chat session this message belongs to"
    )
    
    # Who sent this message
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text="User who sent this message"
    )
    
    # Message type
    message_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_TEXT,
        db_index=True,
        help_text="Type of message"
    )
    
    # Message content
    content = models.TextField(
        help_text="Text content of the message"
    )
    
    # File attachment (if message_type is file or image)
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip']
            )
        ],
        help_text="File attachment"
    )
    
    # Attachment metadata
    attachment_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Original filename of attachment"
    )
    attachment_size = models.IntegerField(
        default=0,
        help_text="Size of attachment in bytes"
    )
    
    # Delivery and read status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_SENT,
        help_text="Delivery status of message"
    )
    
    # Read tracking
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether message has been read"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When message was read"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,  # Index for time-based ordering
        help_text="When message was sent"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When message was last updated"
    )
    
    # Deleted flag (soft delete)
    is_deleted = models.BooleanField(
        default=False,
        help_text="Whether message has been deleted"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When message was deleted"
    )
    
    class Meta:
        ordering = ['created_at']  # Chronological order
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_read', 'session']),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"
    
    def __str__(self):
        return f"Message {self.message_id} in Session {self.session.session_id}"
    
    def mark_as_read(self):
        """
        Mark message as read
        """
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.status = self.STATUS_READ
            self.save(update_fields=['is_read', 'read_at', 'status'])
    
    def mark_as_delivered(self):
        """
        Mark message as delivered
        """
        if self.status == self.STATUS_SENT:
            self.status = self.STATUS_DELIVERED
            self.save(update_fields=['status'])
    
    def soft_delete(self):
        """
        Soft delete message (doesn't actually remove from database)
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])


class TypingIndicator(models.Model):
    """
    Tracks who is currently typing in a chat session
    
    This is a temporary model - records are created/deleted frequently.
    Used to show "Agent is typing..." or "Visitor is typing..." indicators.
    """
    
    # Chat session
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="typing_indicators",
        help_text="Chat session where typing is occurring"
    )
    
    # Who is typing
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User who is typing"
    )
    
    # Timestamp (auto-delete old records)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When typing started"
    )
    
    class Meta:
        unique_together = ('session', 'user')  # One typing indicator per user per session
        ordering = ['-created_at']
        verbose_name = "Typing Indicator"
        verbose_name_plural = "Typing Indicators"
    
    def __str__(self):
        return f"{self.user.username} typing in {self.session.session_id}"


class ChatSessionRating(models.Model):
    """
    Detailed rating and feedback for a chat session
    
    Separate from ChatSession model to allow more detailed feedback structure.
    Can include multiple rating categories.
    """
    
    # Chat session being rated
    session = models.OneToOneField(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="detailed_rating",
        help_text="Chat session being rated"
    )
    
    # Overall rating (1-5 stars)
    overall_rating = models.IntegerField(
        help_text="Overall rating (1-5)"
    )
    
    # Category ratings
    agent_friendliness = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating for agent friendliness (1-5)"
    )
    response_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating for response time (1-5)"
    )
    problem_resolution = models.IntegerField(
        null=True,
        blank=True,
        help_text="Rating for problem resolution (1-5)"
    )
    
    # Feedback text
    feedback = models.TextField(
        blank=True,
        help_text="Detailed feedback from visitor"
    )
    
    # Would recommend?
    would_recommend = models.BooleanField(
        default=False,
        help_text="Would visitor recommend this service"
    )
    
    # Timestamp
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When rating was submitted"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Session Rating"
        verbose_name_plural = "Session Ratings"
    
    def __str__(self):
        return f"Rating for {self.session.session_id} - {self.overall_rating}/5"
    
    