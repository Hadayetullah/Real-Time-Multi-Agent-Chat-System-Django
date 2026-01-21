from django.urls import path
from .views import AgentSignupView, AgentOTPVerifyView, AgentLoginView

urlpatterns = [
    path("agent/signup/", AgentSignupView.as_view()),
    path("agent/verify-otp/", AgentOTPVerifyView.as_view()),
    path("agent/login/", AgentLoginView.as_view()),
]

