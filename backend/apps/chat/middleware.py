# Custom JWT Auth Middleware
from urllib.parse import parse_qs
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token")

        if token:
            try:
                validated = JWTAuthentication().get_validated_token(token[0])
                scope["user"] = JWTAuthentication().get_user(validated)
            except Exception:
                pass

        return await self.app(scope, receive, send)



