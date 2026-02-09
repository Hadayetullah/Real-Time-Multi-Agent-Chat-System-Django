# Channels root routing Setup for WebSocket connections
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from apps.chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<uuid:session_id>/', ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
