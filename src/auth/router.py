"""Authentication router - Google OAuth2 + JWT."""

import uuid
from js import Headers, Response

from auth.google import exchange_code
from auth.jwt_handler import create_token, verify_token
from models.base import row_get
from utils.helpers import cors_headers, error, json_resp, resolve_allowed_origin


def _body_get(data, key: str):
    if isinstance(data, dict):
        return data.get(key)
    return getattr(data, key, None)


async def handle_auth(request, env, path: str):
    try:
        if request.method == "OPTIONS":
            return Response.new(
                None,
                status=204,
                headers=cors_headers(
                    env=env,
                    request=request,
                    content_type=None,
                    allow_credentials=True,
                ),
            )

        # GET /auth/google/login
        if path == "/auth/google/login":
            redirect_url = (
                "https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={env.GOOGLE_CLIENT_ID}"
                "&response_type=code"
                "&scope=openid%20email%20profile"
                f"&redirect_uri={env.FRONTEND_URL}/auth/google/callback"
            )
            headers = Headers.new(
                [
                    ("Location", redirect_url),
                    (
                        "Access-Control-Allow-Origin",
                        resolve_allowed_origin(env, request),
                    ),
                ]
            )
            return Response.new("", status=302, headers=headers)

        # POST /auth/google/callback
        if path == "/auth/google/callback":
            data = await request.json()
            code = _body_get(data, "code")
            if not code:
                return error("Missing code", 400, env=env, request=request)

            user_info = await exchange_code(code, env)
            if not user_info or "error" in user_info:
                return error(
                    "Google authentication failed",
                    401,
                    env=env,
                    request=request,
                )

            google_id = user_info.get("id")
            if not google_id:
                return error(
                    "Invalid user info from Google",
                    400,
                    env=env,
                    request=request,
                )

            user_id = str(uuid.uuid4())
            await (
                env.DB.prepare(
                    "INSERT INTO users (id, email, name, avatar_url, google_id, role)"
                    " VALUES (?, ?, ?, ?, ?, ?)"
                    " ON CONFLICT(google_id) DO UPDATE SET"
                    " name=excluded.name,"
                    " avatar_url=COALESCE(NULLIF(users.avatar_url, ''), excluded.avatar_url),"
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
                    "SELECT id, email, name, role, avatar_url, terms_accepted_at"
                    " FROM users WHERE google_id = ?"
                )
                .bind(google_id)
                .first()
            )
            if not row:
                return error(
                    "User not found after upsert",
                    500,
                    env=env,
                    request=request,
                )

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
                f"refresh:{row_get(row, 'id')}",
                refresh_token,
                expiration_ttl=604800,
            )

            return json_resp(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": row_get(row, "id"),
                        "email": row_get(row, "email"),
                        "name": row_get(row, "name"),
                        "role": row_get(row, "role"),
                        "avatar_url": row_get(row, "avatar_url"),
                        "terms_accepted_at": row_get(
                            row,
                            "terms_accepted_at",
                        ),
                    },
                },
                env=env,
                request=request,
            )

        # POST /auth/refresh
        if path == "/auth/refresh":
            data = await request.json()
            refresh_token = _body_get(data, "refresh_token")
            if not refresh_token:
                return error(
                    "Missing refresh token",
                    400,
                    env=env,
                    request=request,
                )

            payload = verify_token(refresh_token, env.JWT_SECRET)
            if not payload:
                return error(
                    "Invalid refresh token",
                    401,
                    env=env,
                    request=request,
                )

            user_id = payload.get("sub")
            if not user_id:
                return error(
                    "Invalid refresh token",
                    401,
                    env=env,
                    request=request,
                )

            stored = await env.SESSIONS.get(f"refresh:{user_id}")
            if stored != refresh_token:
                return error(
                    "Refresh token revoked",
                    401,
                    env=env,
                    request=request,
                )

            row = (
                await env.DB.prepare("SELECT id, email, role FROM users WHERE id = ?")
                .bind(user_id)
                .first()
            )
            if not row:
                return error("User not found", 404, env=env, request=request)

            access_token = create_token(
                {
                    "sub": row_get(row, "id"),
                    "email": row_get(row, "email"),
                    "role": row_get(row, "role"),
                },
                env.JWT_SECRET,
                expires_in=900,
            )
            return json_resp(
                {"access_token": access_token},
                env=env,
                request=request,
            )

        # POST /auth/logout
        if path == "/auth/logout":
            data = await request.json()
            user_id = _body_get(data, "user_id")
            if user_id:
                await env.SESSIONS.delete(f"refresh:{user_id}")
            return json_resp(
                {"status": "logged out"},
                env=env,
                request=request,
            )

        return error("Not found", 404, env=env, request=request)

    except Exception:
        return error("Internal server error", 500, env=env, request=request)
