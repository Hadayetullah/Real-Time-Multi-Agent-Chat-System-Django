import random
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.chat.models import ChatSession
from apps.users.models import UserProfile
from apps.chat.utils import get_or_create_visitor



class StartChatView(APIView):
    def post(self, request):
        visitor = get_or_create_visitor(request)

        agents = (
            UserProfile.objects
            .filter(role=UserProfile.ROLE_AGENT)
            .annotate(
                active_sessions=Count(
                    "user__agent_sessions",
                    filter=Q(user__agent_sessions__closed_at__isnull=True)
                )
            )
        )

        if not agents.exists():
            return Response({"detail": "No agents available"}, status=503)

        min_count = min(a.active_sessions for a in agents)
        candidate_agents = [a for a in agents if a.active_sessions == min_count]

        selected_agent = random.choice(candidate_agents).user

        session = ChatSession.objects.create(
            visitor=visitor,
            agent=selected_agent
        )

        return Response({"session_id": session.id})




class CloseChatSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        try:
            chat = ChatSession.objects.get(
                id=chat_id,
                agent=request.user
            )
        except ChatSession.DoesNotExist:
            return Response({"detail": "Chat not found"}, status=404)

        chat.status = ChatSession.STATUS_CLOSED
        chat.closed_at = timezone.now()
        chat.save()

        return Response({"detail": "Chat closed successfully"})


