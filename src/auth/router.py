"""Simple authentication router for the Zenos backend.

This module exports a single entry point, :func:`handle_auth`, which is
invoked by the Cloudflare Worker on each HTTP request.  It dispatches
requests based on the URL path and performs the following operations:

* Redirect to Google OAuth2 consent screen (``/auth/google/login``)
* Handle OAuth2 callback and issue JWTs (``/auth/google/callback``)
* Refresh an access token using a stored refresh token
  (``/auth/refresh``)
* Log a user out by revoking a refresh token (``/auth/logout``)

The router depends on an ``env`` object with the following attributes
(set via ``wrangler.toml`` bindings):

* ``GOOGLE_CLIENT_ID``
* ``JWT_SECRET``
* ``FRONTEND_URL``
* ``DB`` – a sqlite database connection
* ``SESSIONS`` – a Cloudflare KV namespace used for refresh tokens

All responses produced by this module are JSON; the helper
:func:`json_response` centralizes header creation.
"""

import json
import uuid
from js import Response, URL, Headers
from .google import exchange_code
from .jwt_handler import create_token, verify_token


def json_response(data: dict, status: int = 200):
    """Return a JSON HTTP response with the given status code.

    Parameters
    ----------
    data : dict
        The object to serialize as JSON.
    status : int, optional
        HTTP status code (default 200).

    Returns
    -------
    Response
        A ``js.Response`` with ``Content-Type: application/json`` and CORS headers.
    """
    headers = Headers.new(
        [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
        ]
    )
    return Response.new(json.dumps(data), status=status, headers=headers)


async def handle_auth(request, env, path: str):
    """Entry point for authentication routes.

    The function inspects the ``path`` argument and executes the
    corresponding logic.  It is intentionally minimal; most of the heavy
    lifting (OAuth code exchange, JWT creation) is delegated to helper
    functions in :mod:`google` and :mod:`jwt_handler`.

    Parameters
    ----------
    request : js.Request
        Incoming HTTP request from the Worker runtime.
    env : typing.Any
        Environment bindings provided by Cloudflare Workers.  See the
        module docstring for expected attributes.
    path : str
        The path component of the URL used to select the operation.

    Returns
    -------
    js.Response
        A JSON response object describing success or failure.
    """
    try:
        if request.method == "OPTIONS":
            headers = Headers.new(
                [
                    ("Access-Control-Allow-Origin", "*"),
                    ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                    ("Access-Control-Allow-Headers", "Content-Type, Authorization"),
                ]
            )
            return Response.new("", status=200, headers=headers)

        # GET /auth/google/login -> redirect to google auth page
        if path == "/auth/google/login":
            # Build Google OAuth2 authorization URL with required scopes and
            # redirect URI.  The front-end will then receive the authorization
            # code and post it back to /auth/google/callback.
            url = URL.new(
                "https://accounts.google.com/o/oauth2/v2/auth"
                f"?client_id={env.GOOGLE_CLIENT_ID}"
                "&response_type=code"
                "&scope=openid%20email%20profile"
                f"&redirect_uri={env.FRONTEND_URL}/auth/google/callback"
            )
            loc_headers = Headers.new(
                [("Location", url), ("Access-Control-Allow-Origin", "*")]
            )
            return Response.new("", status=302, headers=loc_headers)

        # POST /auth/google/callback -> exchange code for token and return JWT
        if path == "/auth/google/callback":
            print("Callback received")
            # read JSON body from the front-end
            data = await request.json()
            code = data.get("code")
            # print(f"Code: {code}")
            if not code:
                return json_response({"error": "Missing code"}, 400)
            try:
                # exchange the authorization code for user info from Google
                user_info = await exchange_code(code, env)
                print(f"User info: {user_info}")
                if not user_info:
                    return json_response({"error": "Google authentication failed"}, 401)
                user_id = str(uuid.uuid4())
                google_id = user_info.get("id")

                if not google_id:
                    # something went wrong, Google didn't return an id
                    return json_response({"error": "Invalid user info"}, 400)

                if env.ENVIRONMENT == "development":
                    # Skip DB operations for local development
                    user_id = str(uuid.uuid4())
                    access_token = create_token(
                        {
                            "sub": user_id,
                            "email": user_info.get("email"),
                            "role": "user",
                        },
                        env.JWT_SECRET,
                        expires_in=900,
                    )
                    refresh_token = create_token(
                        {"sub": user_id, "type": "refresh"},
                        env.JWT_SECRET,
                        expires_in=604800,
                    )
                    return json_response(
                        {
                            "user": {
                                "id": user_id,
                                "email": user_info.get("email"),
                                "name": user_info.get("name"),
                                "role": "user",
                                "avatar_url": user_info.get("avatar_url"),
                            },
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                        }
                    )
                else:
                    # Upsert user record; on conflict update name/avatar
                    await (
                        env.DB.execute(
                            "INSERT INTO users (id, email,avatar_url,google_id,role)"
                            " VALUES (?,?,?,?,?,?) ON CONFLICT(google_id) DO UPDATE SET"
                            " name=excluded.name, avatar_url=excluded.avatar_url"
                        )
                        .bind(
                            user_id,
                            user_info["email"],
                            user_info["name"],
                            user_info.get("picture", ""),
                            google_id,
                            "READER",
                        )
                        .run()
                    )
                    row = (
                        await env.DB.execute("SELECT id FROM users WHERE google_id = ?")
                        .bind(google_id)
                        .first()
                    )

                    # Create JWTs for the client
                    access_token = create_token(
                        {"sub": row["id"], "email": row["email"], "role": row["role"]},
                        env.JWT_SECRET,
                        expires_in=900,
                    )
                    refresh_token = create_token(
                        {"sub": row["id"], "type": "refresh"},
                        env.JWT_SECRET,
                        expires_in=604800,
                    )
                    # Persist refresh token so we can revoke it later
                    await env.SESSIONS.put(
                        f'refresh:{row["id"]}', refresh_token, expiration_ttl=604800
                    )
                return json_response(
                    {
                        "access_token": access_token,
                        "user": {
                            "id": row["id"],
                            "email": row["email"],
                            "name": row["name"],
                            "role": row["role"],
                            "avatar_url": row["avatar_url"],
                        },
                    }
                )

            except Exception as e:
                # unexpected error, return 500 to client
                print(f"Error in Google callback: {e}")
                return json_response({"error": str(e)}, 500)

        # POST /auth/refresh -> exchange refresh token for new access token
        if path == "/auth/refresh":
            # expecting JSON {"refresh_token": "..."}
            data = await request.json()
            refresh_token = data.get("refresh_token")
            if not refresh_token:
                return json_response({"error": "Missing refresh token"}, 400)

            # verify format/signature of the token
            payload = verify_token(refresh_token, env.JWT_SECRET)
            if not payload or payload.get("type") != "refresh":
                return json_response({"error": "Invalid refresh token"}, 401)
            user_id = payload["sub"]

            # ensure token hasn't been revoked by checking KV
            stored_token = await env.SESSIONS.get(f"refresh:{user_id}")
            if stored_token != refresh_token:
                return json_response({"error": "Refresh token revoked"}, 401)

            # load user data for claims
            row = (
                await env.DB.execute("SELECT id,email,role FROM users WHERE id = ?")
                .bind(user_id)
                .first()
            )
            if not row:
                return json_response({"error": "User not found"}, 404)
            access_token = create_token(
                {"sub": row["id"], "email": row["email"], "role": row["role"]},
                env.JWT_SECRET,
                expires_in=900,
            )
            return json_response({"access_token": access_token})

        # POST /auth/logout
        if path == "/auth/logout":
            body = await request.json()
            user_id = (
                body.get("user_id")
                if isinstance(body, dict)
                else getattr(body, "user_id", None)
            )
            if user_id:
                await env.SESSIONS.delete(f"refresh:{user_id}")
            return json_response({"status": "logged out"})
    except Exception as e:
        print(f"Error handling auth request: {e}")

    return json_response({"error": "Not found"}, 404)
