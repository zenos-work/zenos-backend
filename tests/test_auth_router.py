import importlib
import sys
import types

import pytest


if "js" in sys.modules:
    if not hasattr(sys.modules["js"], "fetch"):
        sys.modules["js"].fetch = None
else:
    js_stub = types.ModuleType("js")
    js_stub.fetch = None
    sys.modules["js"] = js_stub


auth_router = importlib.import_module("auth.router")
jwt_handler = importlib.import_module("auth.jwt_handler")


class FakeSessions:
    def __init__(self):
        self.store = {}

    async def put(self, key, value, expiration_ttl=None):
        self.store[key] = value

    async def get(self, key):
        return self.store.get(key)

    async def delete(self, key):
        self.store.pop(key, None)


class FakePrepared:
    def __init__(self, db, sql):
        self.db = db
        self.sql = sql
        self.params = ()

    def bind(self, *args):
        self.params = args
        return self

    async def run(self):
        if "INSERT INTO users" in self.sql:
            user_id, email, name, avatar_url, google_id, role = self.params
            self.db.by_google_id[google_id] = {
                "id": user_id,
                "email": email,
                "name": name,
                "avatar_url": avatar_url,
                "google_id": google_id,
                "role": role,
                "terms_accepted_at": None,
            }
        return None

    async def first(self):
        if "WHERE google_id = ?" in self.sql:
            google_id = self.params[0]
            return self.db.by_google_id.get(google_id)
        if "WHERE id = ?" in self.sql:
            user_id = self.params[0]
            return self.db.by_id.get(user_id)
        return None


class FakeDB:
    def __init__(self):
        self.by_google_id = {}
        self.by_id = {
            "user-123": {
                "id": "user-123",
                "email": "alice@example.com",
                "role": "AUTHOR",
            }
        }

    def prepare(self, sql):
        return FakePrepared(self, sql)


class FakeEnv:
    GOOGLE_CLIENT_ID = "google-client-id"
    FRONTEND_URL = "http://localhost:5173"
    JWT_SECRET = "test-secret"

    def __init__(self):
        self.DB = FakeDB()
        self.SESSIONS = FakeSessions()


class DummyRequest:
    def __init__(self, method="GET", path="/", headers=None, body=None):
        self.method = method
        self.url = f"http://localhost:8787{path}"
        self.headers = headers or {}
        self._body = body or {}

    async def json(self):
        return self._body


@pytest.mark.asyncio
async def test_options_preflight_returns_204():
    env = FakeEnv()
    request = DummyRequest(method="OPTIONS", path="/auth/refresh")

    response = await auth_router.handle_auth(request, env, "/auth/refresh")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_google_login_redirect():
    env = FakeEnv()
    request = DummyRequest(method="GET", path="/auth/google/login")

    response = await auth_router.handle_auth(request, env, "/auth/google/login")

    assert response.status_code == 302
    assert "accounts.google.com" in response.headers["Location"]
    assert "client_id=google-client-id" in response.headers["Location"]


@pytest.mark.asyncio
async def test_google_callback_missing_code_returns_400():
    env = FakeEnv()
    request = DummyRequest(
        method="POST",
        path="/auth/google/callback",
        body={},
    )

    response = await auth_router.handle_auth(request, env, "/auth/google/callback")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


@pytest.mark.asyncio
async def test_google_callback_auth_failed_returns_401(monkeypatch):
    async def fake_exchange_code(code, env):
        return {"error": "invalid_grant"}

    monkeypatch.setattr(auth_router, "exchange_code", fake_exchange_code)

    env = FakeEnv()
    request = DummyRequest(
        method="POST",
        path="/auth/google/callback",
        body={"code": "bad-code"},
    )

    response = await auth_router.handle_auth(request, env, "/auth/google/callback")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORISED"


@pytest.mark.asyncio
async def test_google_callback_success_returns_tokens_and_user(monkeypatch):
    async def fake_exchange_code(code, env):
        return {
            "id": "google-123",
            "email": "alice@example.com",
            "name": "Alice",
            "picture": "https://img.example.com/alice.jpg",
        }

    monkeypatch.setattr(auth_router, "exchange_code", fake_exchange_code)

    env = FakeEnv()
    request = DummyRequest(
        method="POST",
        path="/auth/google/callback",
        body={"code": "good-code"},
    )

    response = await auth_router.handle_auth(request, env, "/auth/google/callback")

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["user"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_refresh_missing_token_returns_400():
    env = FakeEnv()
    request = DummyRequest(method="POST", path="/auth/refresh", body={})

    response = await auth_router.handle_auth(request, env, "/auth/refresh")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BAD_REQUEST"


@pytest.mark.asyncio
async def test_refresh_invalid_token_returns_401():
    env = FakeEnv()
    request = DummyRequest(
        method="POST",
        path="/auth/refresh",
        body={"refresh_token": "invalid.token.here"},
    )

    response = await auth_router.handle_auth(request, env, "/auth/refresh")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORISED"


@pytest.mark.asyncio
async def test_refresh_revoked_token_returns_401():
    env = FakeEnv()
    token = jwt_handler.create_token(
        {"sub": "user-123", "type": "refresh"},
        env.JWT_SECRET,
        expires_in=3600,
    )
    request = DummyRequest(
        method="POST",
        path="/auth/refresh",
        body={"refresh_token": token},
    )

    response = await auth_router.handle_auth(request, env, "/auth/refresh")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORISED"


@pytest.mark.asyncio
async def test_refresh_success_returns_new_access_token():
    env = FakeEnv()
    refresh_token = jwt_handler.create_token(
        {"sub": "user-123", "type": "refresh"},
        env.JWT_SECRET,
        expires_in=3600,
    )
    await env.SESSIONS.put("refresh:user-123", refresh_token)

    request = DummyRequest(
        method="POST",
        path="/auth/refresh",
        body={"refresh_token": refresh_token},
    )

    response = await auth_router.handle_auth(request, env, "/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_logout_deletes_session_token():
    env = FakeEnv()
    await env.SESSIONS.put("refresh:user-123", "token")

    request = DummyRequest(
        method="POST",
        path="/auth/logout",
        body={"user_id": "user-123"},
    )

    response = await auth_router.handle_auth(request, env, "/auth/logout")

    assert response.status_code == 200
    assert response.json()["status"] == "logged out"
    assert "refresh:user-123" not in env.SESSIONS.store


@pytest.mark.asyncio
async def test_unknown_auth_path_returns_404():
    env = FakeEnv()
    request = DummyRequest(method="GET", path="/auth/unknown")

    response = await auth_router.handle_auth(request, env, "/auth/unknown")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
