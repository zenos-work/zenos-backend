import json

from js import Response, Headers
from auth.jwt_handler import verify_token


def require_auth(roles: list = None):
    """Middleware to enforce authentication and optional role-based access control.

    This function checks for a JWT in the Authorization header of the incoming
    request. If a valid token is present, it verifies the token and optionally
    checks if the user has one of the required roles. If authentication fails,
    it returns a 401 Unauthorized response.

    Parameters
    ----------
    roles : list, optional
        A list of roles that are allowed to access the endpoint. If None, any
        authenticated user is allowed.

    Returns
    -------
    function
        A decorator function that can be applied to route handlers.
    """

    def decorator(handler):
        async def wrapper(request, env, *args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            headers = Headers.new(
                [
                    ("Content-Type", "application/json"),
                    ("Access-Control-Allow-Origin", "*"),
                ]
            )
            if not auth_header.startswith("Bearer "):
                return Response.new(
                    json.dumps({"error": "Unauthorized"}),
                    {"status": 401},
                    headers=headers,
                )
            token = auth_header[len("Bearer ") :]
            user_data = verify_token(token, env.JWT_SECRET)
            if not user_data:
                return Response.new(
                    json.dumps({"error": "Token expired"}),
                    {"status": 401},
                    headers=headers,
                )
            if roles and user_data.get("role") not in roles:
                return Response.new(
                    json.dumps({"error": "Forbidden"}), {"status": 403}, headers=headers
                )
            request.user = user_data  # Attach user data to request for handler use
            return await handler(request, env, *args, **kwargs)

        return wrapper

    return decorator
