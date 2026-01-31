from django.urls import path
from .views import StartChatView, CloseChatSessionAPIView


urlpatterns = [
    path("start/", StartChatView.as_view(), name="start-chat"),
    path(
        "chats/<int:chat_id>/close/",
        CloseChatSessionAPIView.as_view(),
        name="close-chat",
    ),
]
