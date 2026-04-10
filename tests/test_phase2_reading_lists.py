"""Tests for Phase 2 Step 14 — Reading Lists (model + service + handler)."""

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

rl_models = importlib.import_module("models.reading_list.model")
ReadingList = rl_models.ReadingList
ReadingListItem = rl_models.ReadingListItem
reading_list_handler = importlib.import_module("api.reading_lists.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestReadingListModels:
    def test_reading_list_from_row(self):
        row = {
            "id": "rl1",
            "user_id": "u1",
            "name": "Fintech",
            "is_public": 1,
            "is_default": 0,
            "article_count": 3,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "description": "My fintech reads",
            "cover_image_url": None,
        }
        rl = ReadingList.from_row(row)
        assert rl.name == "Fintech"
        assert rl.article_count == 3

    def test_reading_list_to_dict(self):
        rl = ReadingList(
            id="rl1",
            user_id="u1",
            name="Fintech",
            is_public=1,
            is_default=0,
            article_count=3,
            created_at="2026-01-01",
            updated_at="2026-01-01",
            description="My reads",
        )
        d = rl.to_dict()
        assert d["is_public"] is True
        assert d["article_count"] == 3

    def test_reading_list_item_from_row(self):
        row = {
            "id": "rli1",
            "list_id": "rl1",
            "article_id": "a1",
            "sort_order": 1,
            "added_at": "2026-01-01",
            "note": "Good article",
        }
        item = ReadingListItem.from_row(row)
        assert item.article_id == "a1"
        assert item.note == "Good article"

    def test_reading_list_item_to_dict(self):
        item = ReadingListItem(
            id="rli1",
            list_id="rl1",
            article_id="a1",
            sort_order=1,
            added_at="2026-01-01",
        )
        d = item.to_dict()
        assert d["article_id"] == "a1"
        assert "note" not in d  # None excluded


# ── Fake Service ──
class FakeReadingListService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def create_list(
        self, user_id, name, description=None, cover_image_url=None, is_public=False
    ):
        self.calls.append(("create_list", user_id, name))
        if not name.strip():
            raise ValueError("Name is required")
        return "new-rl-id"

    async def get_lists(self, user_id, page=1, limit=20):
        self.calls.append(("get_lists", user_id))
        return {
            "reading_lists": [{"id": "rl1", "name": "Fintech"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def get_list_with_items(self, list_id, user_id):
        self.calls.append(("get_list_with_items", list_id))
        if list_id == "missing":
            raise ValueError("Reading list not found")
        return {
            "id": list_id,
            "name": "Fintech",
            "items": [{"id": "rli1", "article_id": "a1"}],
        }

    async def update_list(
        self,
        list_id,
        user_id,
        name,
        description=None,
        cover_image_url=None,
        is_public=False,
    ):
        self.calls.append(("update_list", list_id, name))
        if list_id == "missing":
            raise ValueError("Reading list not found")

    async def delete_list(self, list_id, user_id):
        self.calls.append(("delete_list", list_id))
        if list_id == "missing":
            raise ValueError("Reading list not found")
        if list_id == "default":
            raise ValueError("Cannot delete default reading list")

    async def add_article(self, list_id, article_id, user_id, note=None):
        self.calls.append(("add_article", list_id, article_id))
        if list_id == "missing":
            raise ValueError("Reading list not found")
        return "new-item-id"

    async def remove_article(self, list_id, article_id, user_id):
        self.calls.append(("remove_article", list_id, article_id))
        if list_id == "missing":
            raise ValueError("Reading list not found")


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


class ReadingListClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

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

        orig = reading_list_handler.ReadingListService
        reading_list_handler.ReadingListService = _make_svc
        try:
            return asyncio.run(
                reading_list_handler.handle_reading_lists(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            reading_list_handler.ReadingListService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeReadingListService(_Env())


@pytest.fixture
def client(svc):
    return ReadingListClient(svc)


# ── Handler Tests ──
class TestReadingListHandler:
    def test_create_list(self, client, svc):
        resp = client.post(
            "/api/reading-lists",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "Fintech"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-rl-id"

    def test_create_list_empty_name(self, client, svc):
        resp = client.post(
            "/api/reading-lists",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": " "},
        )
        assert resp.status_code == 400

    def test_list_reading_lists(self, client, svc):
        resp = client.get(
            "/api/reading-lists",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "reading_lists" in resp.json()

    def test_get_list_with_items(self, client, svc):
        resp = client.get(
            "/api/reading-lists/rl1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_get_missing_list(self, client, svc):
        resp = client.get(
            "/api/reading-lists/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_update_list(self, client, svc):
        resp = client.put(
            "/api/reading-lists/rl1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "Updated Name"},
        )
        assert resp.status_code == 200

    def test_delete_list(self, client, svc):
        resp = client.delete(
            "/api/reading-lists/rl1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_default_list(self, client, svc):
        resp = client.delete(
            "/api/reading-lists/default",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 400

    def test_add_article(self, client, svc):
        resp = client.post(
            "/api/reading-lists/rl1/articles/a1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={},
        )
        assert resp.status_code == 201

    def test_remove_article(self, client, svc):
        resp = client.delete(
            "/api/reading-lists/rl1/articles/a1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "removed"

    def test_unauth(self, client):
        resp = client.get("/api/reading-lists")
        assert resp.status_code == 401
