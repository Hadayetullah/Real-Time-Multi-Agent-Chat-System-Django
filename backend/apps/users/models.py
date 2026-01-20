from django.conf import settings
from django.db import models


# Create your models here.

class UserProfile(models.Model):
    ROLE_VISITOR = "visitor"
    ROLE_AGENT = "agent"

    ROLE_CHOICES = (
        (ROLE_VISITOR, "Visitor"),
        (ROLE_AGENT, "Agent"),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    is_available = models.BooleanField(default=False) #Applies only to agents

    def __str__(self):
        return f"{self.user.username} ({self.role})"
