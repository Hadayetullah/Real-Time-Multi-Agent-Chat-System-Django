# from django.urls import path
# from .views import StartChatView, CloseChatSessionAPIView


# urlpatterns = [
#     path("start/", StartChatView.as_view(), name="start-chat"),
#     path(
#         "chats/<int:chat_id>/close/",
#         CloseChatSessionAPIView.as_view(),
#         name="close-chat",
#     ),
# ]


from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ChatSessionViewSet, MessageViewSet

# Create router for ViewSets
router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chat-session')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]
