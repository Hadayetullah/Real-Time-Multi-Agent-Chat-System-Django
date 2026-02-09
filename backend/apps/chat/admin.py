from django.contrib import admin
from .models import ChatSession, Message

# Register your models here.

admin.site.register(ChatSession)
admin.site.register(Message)


# @admin.register(ChatSession)
# class ChatSessionAdmin(admin.ModelAdmin):
#     list_display = ("id", "visitor", "agent", "created_at", "closed_at")


# @admin.register(Message)
# class MessageAdmin(admin.ModelAdmin):
#     list_display = ("id", "session", "sender", "created_at")

