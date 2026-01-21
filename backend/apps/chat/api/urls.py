from django.urls import path
from .views import StartChatView

urlpatterns = [
    path("start/", StartChatView.as_view()),
]
