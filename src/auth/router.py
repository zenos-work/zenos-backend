"""Authentication router — Google OAuth2 + JWT."""

import json
import uuid
from js import Response, Headers
from auth.google import exchange_code
from auth.jwt_handler import create_token, verify_token


def json_response(data: dict, status: int = 200):
    headers = Headers.new(
        [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "http://localhost:5173"),
            ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
        ]
    )
    return Response.new(json.dumps(data), status=status, headers=headers)


async def handle_auth(request, env, path: str):
    try:
        if request.method == "OPTIONS":
            headers = Headers.new(
                [
                    ("Access-Control-Allow-Origin", "http://localhost:5173"),
                    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE"),
                    ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
                ]
            )
            return Response.new(None, status=204, headers=headers)

        # GET /auth/google/login
        if path == "/auth/google/login":
            redirect_url = (
                "https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={env.GOOGLE_CLIENT_ID}"
                "&response_type=code"
                "&scope=openid%20email%20profile"
                f"&redirect_uri={env.FRONTEND_URL}/auth/google/callback"
            )
            print(f"Redirecting to Google OAuth2: {redirect_url}")
            loc_headers = Headers.new(
                [
                    ("Location", redirect_url),
                    ("Access-Control-Allow-Origin", "*"),
                ]
            )
            return Response.new("", status=302, headers=loc_headers)

        # POST /auth/google/callback
        if path == "/auth/google/callback":
            print("Handling Google OAuth2 callback")
            data = await request.json()
            # FIX: data from request.json() may be a JS proxy — use dict or attr access
            print(f"Received callback data: {data}")
            code = (
                data.get("code")
                if isinstance(data, dict)
                else getattr(data, "code", None)
            )
            if not code:
                return json_response({"error": "Missing code"}, 400)

            user_info = await exchange_code(code, env)
            if not user_info or "error" in user_info:
                return json_response({"error": "Google authentication failed"}, 401)

            google_id = user_info.get("id")
            if not google_id:
                return json_response({"error": "Invalid user info from Google"}, 400)

            user_id = str(uuid.uuid4())
            print(f"Upserting user {user_info['email']} with Google ID {google_id}")
            await (
                env.DB.prepare(
                    "INSERT INTO users (id, email, name, avatar_url, google_id, role)"
                    " VALUES (?, ?, ?, ?, ?, ?)"
                    " ON CONFLICT(google_id) DO UPDATE SET"
                    " name=excluded.name, avatar_url=excluded.avatar_url,"
                    " updated_at=datetime('now')"
                )
                .bind(
                    user_id,
                    user_info["email"],
                    user_info["name"],
                    user_info.get("picture", ""),
                    google_id,
                    "AUTHOR",
                )
                .run()
            )

            row = (
                await env.DB.prepare(
                    "SELECT id, email, name, role, avatar_url FROM users WHERE google_id = ?"
                )
                .bind(google_id)
                .first()
            )

            if not row:
                return json_response({"error": "User not found after upsert"}, 500)

            from models.base import row_get

            print(f"Retrieved user data for {row_get(row,'email')}")
            access_token = create_token(
                {
                    "sub": row_get(row, "id"),
                    "email": row_get(row, "email"),
                    "role": row_get(row, "role"),
                },
                env.JWT_SECRET,
                expires_in=900,
            )
            refresh_token = create_token(
                {"sub": row_get(row, "id"), "type": "refresh"},
                env.JWT_SECRET,
                expires_in=604800,
            )
            await env.SESSIONS.put(
                f'refresh:{row_get(row,"id")}', refresh_token, expiration_ttl=604800
            )
            return json_response(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": row_get(row, "id"),
                        "email": row_get(row, "email"),
                        "name": row_get(row, "name"),
                        "role": row_get(row, "role"),
                        "avatar_url": row_get(row, "avatar_url"),
                    },
                }
            )

        # POST /auth/refresh
        if path == "/auth/refresh":
            data = await request.json()
            refresh_token = (
                data.get("refresh_token")
                if isinstance(data, dict)
                else getattr(data, "refresh_token", None)
            )
            if not refresh_token:
                return json_response({"error": "Missing refresh token"}, 400)

            payload = verify_token(refresh_token, env.JWT_SECRET)
            if not payload or payload.get("type") != "refresh":
                return json_response({"error": "Invalid refresh token"}, 401)

            user_id = payload["sub"]
            stored = await env.SESSIONS.get(f"refresh:{user_id}")
            if stored != refresh_token:
                return json_response({"error": "Refresh token revoked"}, 401)

            row = (
                await env.DB.prepare("SELECT id, email, role FROM users WHERE id = ?")
                .bind(user_id)
                .first()
            )
            if not row:
                return json_response({"error": "User not found"}, 404)

            from models.base import row_get

            access_token = create_token(
                {
                    "sub": row_get(row, "id"),
                    "email": row_get(row, "email"),
                    "role": row_get(row, "role"),
                },
                env.JWT_SECRET,
                expires_in=900,
            )
            return json_response({"access_token": access_token})

        # POST /auth/logout
        if path == "/auth/logout":
            data = await request.json()
            user_id = (
                data.get("user_id")
                if isinstance(data, dict)
                else getattr(data, "user_id", None)
            )
            if user_id:
                await env.SESSIONS.delete(f"refresh:{user_id}")
            return json_response({"status": "logged out"})

    except Exception as e:
        print(f"Auth error on {path}: {e}")
        return json_response({"error": "Internal server error"}, 500)

    return json_response({"error": "Not found"}, 404)
