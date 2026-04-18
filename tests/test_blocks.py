"""Tests for Phase 2 Step 9 — User Blocks (model + service + handler)."""

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

UserBlock = importlib.import_module("models.block.model").UserBlock
block_handler = importlib.import_module("api.blocks.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestUserBlockModel:
    def test_from_row(self):
        row = {
            "blocker_id": "u1",
            "blocked_id": "u2",
            "block_type": "block",
            "reason": "spam",
            "created_at": "2026-01-01",
        }
        b = UserBlock.from_row(row)
        assert b.blocker_id == "u1"
        assert b.blocked_id == "u2"
        assert b.block_type == "block"

    def test_to_dict(self):
        b = UserBlock(
            blocker_id="u1",
            blocked_id="u2",
            block_type="block",
            reason="spam",
            created_at="2026-01-01",
        )
        d = b.to_dict()
        assert d["blocked_id"] == "u2"
        assert d["block_type"] == "block"


# ── Fake Service ──
class FakeBlockService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def block_user(self, blocker_id, blocked_id, reason=None):
        self.calls.append(("block_user", blocker_id, blocked_id))
        if blocker_id == blocked_id:
            raise ValueError("Cannot block yourself")
        if blocked_id == "already":
            raise ValueError("User already blocked")

    async def unblock_user(self, blocker_id, blocked_id):
        self.calls.append(("unblock_user", blocker_id, blocked_id))

    async def mute_user(self, blocker_id, blocked_id, reason=None):
        self.calls.append(("mute_user", blocker_id, blocked_id))
        if blocker_id == blocked_id:
            raise ValueError("Cannot mute yourself")

    async def unmute_user(self, blocker_id, blocked_id):
        self.calls.append(("unmute_user", blocker_id, blocked_id))

    async def list_blocked(self, user_id, page=1, limit=20):
        self.calls.append(("list_blocked", user_id))
        return {
            "data": [{"blocked_id": "u2", "block_type": "block"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def list_muted(self, user_id, page=1, limit=20):
        self.calls.append(("list_muted", user_id))
        return {
            "data": [{"blocked_id": "u3", "block_type": "mute"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }


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


class BlockClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )
        svc = self.svc

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return svc

        orig = block_handler.BlockService
        block_handler.BlockService = _make_svc
        try:
            return asyncio.run(
                block_handler.handle_blocks(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            block_handler.BlockService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeBlockService(_Env())


@pytest.fixture
def client(svc):
    return BlockClient(svc)


# ── Handler Tests ──
class TestBlockHandler:
    def test_block_user(self, client, svc):
        resp = client.post(
            "/api/users/me/blocks/target-user",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"reason": "spam"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "blocked"

    def test_block_already_blocked(self, client, svc):
        resp = client.post(
            "/api/users/me/blocks/already",
            headers={"Authorization": f"Bearer {_token()}"},
            json={},
        )
        assert resp.status_code == 409

    def test_unblock_user(self, client, svc):
        resp = client.delete(
            "/api/users/me/blocks/target-user",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "unblocked"

    def test_list_blocked(self, client, svc):
        resp = client.get(
            "/api/users/me/blocks",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_mute_user(self, client, svc):
        resp = client.post(
            "/api/users/me/mutes/target-user",
            headers={"Authorization": f"Bearer {_token()}"},
            json={},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "muted"

    def test_unmute_user(self, client, svc):
        resp = client.delete(
            "/api/users/me/mutes/target-user",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "unmuted"

    def test_list_muted(self, client, svc):
        resp = client.get(
            "/api/users/me/mutes",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_unauth(self, client):
        resp = client.get("/api/users/me/blocks")
        assert resp.status_code == 401
