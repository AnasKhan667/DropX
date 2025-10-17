from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

print("🔹 JWT Middleware Loaded!")  # middleware load hone ka proof

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        print("🔹 Incoming WebSocket request!")  # websocket connection ka proof
        query_string = parse_qs(scope["query_string"].decode())
        print("🔹 Raw Query:", query_string)

        token = query_string.get("token")
        if token:
            print("🔹 Token mil gaya:", token[0])
            try:
                access_token = AccessToken(token[0])
                print("✅ Token valid:", access_token)
                user = await database_sync_to_async(User.objects.get)(
                    id=access_token["user_id"]
                )
                print("✅ User mila:", user)
                scope["user"] = user
            except Exception as e:
                print("❌ Token decode error:", e)
                scope["user"] = None
        else:
            print("⚠️ Token missing")
            scope["user"] = None

        return await super().__call__(scope, receive, send)
