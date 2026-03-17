from typing import Optional
from auth.jwt_handler import verify_token


async def get_user(request, env) -> Optional[dict]:
    """Extract and verify JWT from Authorization header. Returns payload or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return verify_token(header[7:], env.JWT_SECRET)


def require_role(user: dict, allowed_roles: tuple | list) -> bool:
    """True if the user's role is in allowed_roles."""
    return user is not None and user.get("role") in allowed_roles
