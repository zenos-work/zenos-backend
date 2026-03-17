import json
import uuid
import re
import math
from js import Headers, Response


def json_resp(data, status: int = 200):
    headers = Headers.new(
        [
            ("Content-Type", "application/json"),
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
        ]
    )
    return Response.new(json.dumps(data), status=status, headers=headers)


def error(message: str, status: int = 400):
    """Structured error response. All API errors use this shape."""
    return json_resp(
        {
            "error": {
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
        },
        status,
    )


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
