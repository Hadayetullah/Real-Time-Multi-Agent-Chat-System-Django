# Custom JWT Auth Middleware
from urllib.parse import parse_qs

from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def get_user_from_jwt(token):
    auth = JWTAuthentication()
    validated_token = auth.get_validated_token(token)
    return auth.get_user(validated_token)


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        token_list = params.get("token")
        if token_list:
            try:
                user = await get_user_from_jwt(token_list[0])
                scope["user"] = user
            except Exception:
                pass

        return await self.inner(scope, receive, send)



