import json
import uuid
import re
import math
import inspect
from urllib.parse import urlsplit
from js import Headers, Response


def _json_default(value):
    # Cloudflare Python Workers can surface JS bridge objects (JsProxy).
    # Convert them to native Python values before encoding JSON.
    to_py = getattr(value, "to_py", None)
    if callable(to_py):
        try:
            return to_py()
        except TypeError:
            return to_py(depth=5)
    raise TypeError(
        f"Object of type {value.__class__.__name__} is not JSON serializable"
    )


def _frontend_origin(env) -> str:
    frontend_url = getattr(env, "FRONTEND_URL", None) if env else None
    if not frontend_url:
        return "*"

    parts = urlsplit(frontend_url)
    if parts.scheme and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return frontend_url


def resolve_allowed_origin(env=None, request=None) -> str:
    configured = _frontend_origin(env)
    request_origin = None
    if request and getattr(request, "headers", None):
        request_origin = request.headers.get("Origin")
        if inspect.isawaitable(request_origin):
            close = getattr(request_origin, "close", None)
            if callable(close):
                close()
            request_origin = None

    if configured == "*" or not request_origin:
        return configured

    return request_origin if request_origin == configured else configured


def cors_headers(
    env=None,
    request=None,
    *,
    content_type: str | None = "application/json",
    methods: str = "GET,POST,PUT,DELETE,OPTIONS,PATCH",
    allow_credentials: bool = False,
    extra_headers: list[tuple[str, str]] | None = None,
):
    header_items = []
    if content_type:
        header_items.append(("Content-Type", content_type))
    header_items.extend(
        [
            ("Access-Control-Allow-Origin", resolve_allowed_origin(env, request)),
            ("Access-Control-Allow-Methods", methods),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
        ]
    )
    if allow_credentials:
        header_items.append(("Access-Control-Allow-Credentials", "true"))
    if extra_headers:
        header_items.extend(extra_headers)
    return Headers.new(header_items)


def json_resp(data, status: int = 200, env=None, request=None):
    headers = cors_headers(env=env, request=request)
    return Response.new(
        json.dumps(data, default=_json_default),
        status=status,
        headers=headers,
    )


def error(
    message: str,
    status: int = 400,
    details: dict | None = None,
    env=None,
    request=None,
):
    """Structured error response. All API errors use this shape."""
    payload = {
        "message": message,
        "status": status,
        "code": {
            400: "BAD_REQUEST",
            401: "UNAUTHORISED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            500: "INTERNAL_ERROR",
        }.get(status, "ERROR"),
    }
    if details:
        payload.update(details)
    return json_resp({"error": payload}, status, env=env, request=request)


def new_id() -> str:
    return str(uuid.uuid4())


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower().strip())
    return re.sub(r"[\s_-]+", "-", text)[:100]


def unique_slug(title: str) -> str:
    return f"{slugify(title)}-{new_id()[:8]}"


def calc_read_time(content: str, wpm: int = 200) -> int:
    return max(1, math.ceil(len(content.split()) / wpm))


def paginate(page: int = 1, limit: int = 20) -> tuple:
    page = max(1, page)
    limit = min(100, max(1, limit))
    return limit, (page - 1) * limit
