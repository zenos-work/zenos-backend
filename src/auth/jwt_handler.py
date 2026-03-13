import json
import hmac
import hashlib
import base64
import time
from typing import Optional


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64d(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * pad)


def create_token(payload: dict, secret: str, expires_in: int = 900) -> str:
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload["exp"] = int(time.time()) + expires_in
    body = _b64(json.dumps(payload).encode())
    sig = _b64(
        hmac.new(secret.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest()
    )
    return f"{header}.{body}.{sig}"


def verify_token(token: str, secret: str) -> Optional[dict]:
    try:
        header, body, sig = token.split(".")
        expected = _b64(
            hmac.new(
                secret.encode(), f"{header}.{body}".encode(), hashlib.sha256
            ).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(_b64d(body))
        if data.get("exp", 0) < time.time():
            return None

        return data
    except Exception:
        return None
