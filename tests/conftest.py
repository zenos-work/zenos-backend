import asyncio
import importlib
import json
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
    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(values=None, **_kwargs):
            if values is None:
                return {}
            if isinstance(values, dict):
                return values
            return {key: value for key, value in values}

    class _ResponseInstance:
        def __init__(self, body=None, status=200, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self._body = body

        def json(self):
            if self._body is None or self._body == "":
                return None
            if isinstance(self._body, (dict, list)):
                return self._body
            return json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _ResponseInstance(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub


User = importlib.import_module("models.user.model").User
create_token = importlib.import_module("auth.jwt_handler").create_token
users_handler = importlib.import_module("api.users.handler")


def _build_users():
    return {
        "user-123": User(
            id="user-123",
            email="alice@example.com",
            name="Alice Author",
            role="AUTHOR",
            avatar_url="https://media.zenos.work/uploads/avatar.jpg",
            google_id="google-id-456",
            is_active=1,
            created_at="2026-01-15T10:30:00Z",
            updated_at="2026-03-16T14:22:00Z",
        ),
        "auth-user": User(
            id="auth-user",
            email="writer@example.com",
            name="Writer User",
            role="AUTHOR",
            avatar_url="https://media.zenos.work/uploads/writer.jpg",
            google_id="google-writer-1",
            is_active=1,
            created_at="2026-02-01T08:00:00Z",
            updated_at="2026-03-18T09:00:00Z",
            terms_accepted_at="2026-03-18T10:00:00Z",
        ),
        "reader-user": User(
            id="reader-user",
            email="reader@example.com",
            name="Reader User",
            role="READER",
            avatar_url=None,
            google_id="google-reader-1",
            is_active=1,
            created_at="2026-02-10T08:00:00Z",
            updated_at="2026-03-18T09:00:00Z",
        ),
        "approver-user": User(
            id="approver-user",
            email="approver@example.com",
            name="Approver User",
            role="APPROVER",
            avatar_url=None,
            google_id="google-approver-1",
            is_active=1,
            created_at="2026-02-11T08:00:00Z",
            updated_at="2026-03-18T09:00:00Z",
        ),
        "superadmin-user": User(
            id="superadmin-user",
            email="superadmin@example.com",
            name="Superadmin User",
            role="SUPERADMIN",
            avatar_url=None,
            google_id="google-superadmin-1",
            is_active=1,
            created_at="2026-02-12T08:00:00Z",
            updated_at="2026-03-18T09:00:00Z",
        ),
    }


class FakePreparedStatement:
    def __init__(self, state, sql):
        self.state = state
        self.sql = sql
        self.params = ()

    def bind(self, *args):
        self.params = args
        return self

    async def run(self):
        if "UPDATE users" in self.sql and "terms_accepted_at" in self.sql:
            user = self.state["users"][self.params[0]]
            if user.terms_accepted_at is None:
                user.terms_accepted_at = "2026-03-18T12:00:00Z"
        return None

    async def first(self):
        if "SELECT terms_accepted_at FROM users WHERE id = ?" in self.sql:
            user = self.state["users"][self.params[0]]
            return {"terms_accepted_at": user.terms_accepted_at}
        return None


class FakeDB:
    def __init__(self, state):
        self.state = state

    def prepare(self, sql):
        return FakePreparedStatement(self.state, sql)


class FakeUserService:
    def __init__(self, env, ctx):
        self.env = env
        self.ctx = ctx
        self.state = env.state

    async def get_by_id(self, user_id, scope=None):
        return self.state["users"].get(user_id)

    async def list_all(self, limit, offset):
        users = [
            user.to_dict() for user in self.state["users"].values() if user.is_active
        ]
        return users[offset : offset + limit], len(users)

    async def update_profile(self, user_id, req, skip_name_update=False):
        user = self.state["users"][user_id]
        if not skip_name_update and getattr(req, "name", None) is not None:
            user.name = req.name
        user.avatar_url = getattr(req, "avatar_url", None)
        self.state["profile_updates"].append(
            {
                "user_id": user_id,
                "name": getattr(req, "name", None),
                "avatar_url": getattr(req, "avatar_url", None),
                "skip_name_update": skip_name_update,
            }
        )
        return self.state["profile_updates"][-1]

    async def set_role(self, user_id, req):
        self.state["users"][user_id].role = req.role
        return {"user_id": user_id, "role": req.role}

    async def ban(self, user_id):
        self.state["users"][user_id].is_active = 0
        return {"user_id": user_id, "is_active": False}

    async def unban(self, user_id):
        self.state["users"][user_id].is_active = 1
        return {"user_id": user_id, "is_active": True}

    async def get_prefs(self, user_id):
        return {"topics": ["fintech"], "user_id": user_id}

    async def update_prefs(self, user_id, topics, email_notifs, theme):
        return {
            "user_id": user_id,
            "topics": topics,
            "email_notifs": email_notifs,
            "theme": theme,
        }

    async def self_upgrade_to_author(self, user_id):
        return {"user_id": user_id, "role": "AUTHOR"}


class FakeMediaService:
    def __init__(self, env, ctx):
        self.env = env
        self.ctx = ctx

    async def upload(self, user_id, request):
        self.env.state["uploads"].append(
            {
                "user_id": user_id,
                "content_type": request.headers.get("Content-Type"),
                "body": request.body,
            }
        )
        return {
            "url": f"https://media.zenos.work/uploads/{user_id}.jpg",
            "key": f"uploads/{user_id}.jpg",
        }


class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None, data=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json_body = json_body
        self.body = data if data is not None else json_body

    async def json(self):
        return self._json_body if self._json_body is not None else {}


class FakeEnv:
    JWT_SECRET = "test-secret"

    def __init__(self):
        self.state = {
            "users": _build_users(),
            "profile_updates": [],
            "uploads": [],
        }
        self.DB = FakeDB(self.state)


class FakeCtx:
    trace_id = "test-trace-id"


class UsersClient:
    def __init__(self, env):
        self.env = env

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

    def post(self, path, headers=None, json=None, data=None):
        return self._dispatch("POST", path, headers=headers, json_body=json, data=data)

    def delete(self, path, headers=None, json=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json)

    def _dispatch(self, method, path, headers=None, json_body=None, data=None):
        parsed = urlparse(path)
        request = FakeRequest(
            method=method,
            url=path,
            headers=headers,
            json_body=json_body,
            data=data,
        )
        return asyncio.run(
            users_handler.handle_users(
                request,
                self.env,
                parsed.path,
                method,
                parse_qs(parsed.query),
                FakeCtx(),
            )
        )


@pytest.fixture(autouse=True)
def stub_user_endpoints(monkeypatch):
    monkeypatch.setattr(users_handler, "UserService", FakeUserService)
    monkeypatch.setattr(users_handler, "MediaService", FakeMediaService)


@pytest.fixture
def fake_env():
    return FakeEnv()


@pytest.fixture
def client(fake_env):
    return UsersClient(fake_env)


@pytest.fixture
def auth_token():
    return create_token({"sub": "auth-user", "role": "AUTHOR"}, FakeEnv.JWT_SECRET)


@pytest.fixture
def auth_token_reader():
    return create_token({"sub": "reader-user", "role": "READER"}, FakeEnv.JWT_SECRET)


@pytest.fixture
def auth_token_approver():
    return create_token(
        {"sub": "approver-user", "role": "APPROVER"}, FakeEnv.JWT_SECRET
    )


@pytest.fixture
def auth_token_superadmin():
    return create_token(
        {"sub": "superadmin-user", "role": "SUPERADMIN"}, FakeEnv.JWT_SECRET
    )
