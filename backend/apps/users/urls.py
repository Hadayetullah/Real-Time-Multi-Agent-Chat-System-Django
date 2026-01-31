from django.urls import path
from .views import AgentSignupView, AgentOTPVerifyView, AgentLoginView, ResendOTPView

urlpatterns = [
    path("agent/signup/", AgentSignupView.as_view(), name="agent-signup"),
    path("agent/verify-otp/", AgentOTPVerifyView.as_view(), name="agent-verify-otp"),
    path("agent/login/", AgentLoginView.as_view(), name="agent-login"),
    path("agent/resend-otp/", ResendOTPView.as_view(), name="agent-resend-otp"),
]
