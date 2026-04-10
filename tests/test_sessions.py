"""Tests for Phase 2 Step 8 — User Sessions (model + service + handler)."""

import asyncio
import importlib
import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "js" not in sys.modules:
    import json as _json

    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(values=None, **_kwargs):
            return (
                dict(values)
                if isinstance(values, dict)
                else ({} if values is None else {k: v for k, v in values})
            )

    class _Resp:
        def __init__(self, body=None, status=200, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self._body = body

        def json(self):
            if self._body is None or self._body == "":
                return None
            if isinstance(self._body, (dict, list)):
                return self._body
            return _json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Resp(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub

UserSession = importlib.import_module("models.session.model").UserSession
session_handler = importlib.import_module("api.sessions.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestUserSessionModel:
    def test_from_row(self):
        row = {
            "id": "s1",
            "user_id": "u1",
            "device_info": "Chrome/Win",
            "ip_hash": "abc",
            "country_code": "US",
            "login_method": "google_oauth",
            "last_active_at": "2026-01-01T00:00:00Z",
            "expires_at": "2026-02-01T00:00:00Z",
            "is_revoked": 0,
            "revoked_at": None,
            "revoked_reason": None,
            "created_at": "2026-01-01T00:00:00Z",
        }

        s = UserSession.from_row(row)
        assert s.id == "s1"
        assert s.user_id == "u1"
        assert s.device_info == "Chrome/Win"
        assert s.login_method == "google_oauth"

    def test_to_dict_excludes_private(self):
        s = UserSession(
            id="s1",
            user_id="u1",
            device_info="Chrome",
            ip_hash="abc",
            country_code="US",
            login_method="google_oauth",
            last_active_at="2026-01-01",
            expires_at="2026-02-01",
            is_revoked=0,
            revoked_at=None,
            revoked_reason=None,
            created_at="2026-01-01",
        )
        d = s.to_dict()
        assert "ip_hash" not in d
        assert "user_id" not in d
        assert d["id"] == "s1"
        assert d["device_info"] == "Chrome"


# ── Fake Service for Handler Tests ──
class FakeSessionService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_sessions(self, user_id, page=1, limit=20):
        self.calls.append(("list_sessions", user_id, page, limit))
        return {
            "sessions": [{"id": "s1", "device_info": "Chrome"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def revoke_session(self, session_id, user_id, reason="user_revoked"):
        self.calls.append(("revoke_session", session_id, user_id))
        if session_id == "missing":
            raise ValueError("Session not found")

    async def touch_session(self, session_id):
        self.calls.append(("touch_session", session_id))


class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json = json_body

    async def json(self):
        return self._json or {}


class FakeCtx:
    trace_id = "test-trace"


class SessionClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)

    def _dispatch(self, method, path, headers=None):
        parsed = urlparse(path)
        req = FakeRequest(method=method, url=path, headers=headers or {})
        svc = self.svc

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return svc

        orig = session_handler.SessionService
        session_handler.SessionService = _make_svc
        try:
            return asyncio.run(
                session_handler.handle_sessions(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            session_handler.SessionService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeSessionService(_Env())


@pytest.fixture
def client(svc):
    return SessionClient(svc)


# ── Handler Tests ──
class TestSessionHandler:
    def test_list_sessions(self, client, svc):
        resp = client.get(
            "/api/users/me/sessions", headers={"Authorization": f"Bearer {_token()}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert svc.calls[0][0] == "list_sessions"

    def test_revoke_session(self, client, svc):
        resp = client.delete(
            "/api/users/me/sessions/s1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "revoked"

    def test_revoke_missing_session(self, client, svc):
        resp = client.delete(
            "/api/users/me/sessions/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_unauth(self, client):
        resp = client.get("/api/users/me/sessions")
        assert resp.status_code == 401
