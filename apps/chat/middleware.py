import logging
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """WebSocket middleware that authenticates users via JWT passed as a query param."""

    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token_list = query_string.get("token")

        if token_list:
            try:
                access_token = AccessToken(token_list[0])
                user = await database_sync_to_async(User.objects.get)(
                    id=access_token["user_id"]
                )
                scope["user"] = user
                logger.debug(f"WebSocket authenticated user: {user}")
            except Exception as e:
                logger.warning(f"WebSocket JWT authentication failed: {e}")
                scope["user"] = None
        else:
            logger.debug("WebSocket connection received without a token.")
            scope["user"] = None

        return await super().__call__(scope, receive, send)
