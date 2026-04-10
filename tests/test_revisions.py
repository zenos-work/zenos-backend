"""Tests for Phase 2 Step 10 — Article Revisions (model + service + handler)."""

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

ArticleRevision = importlib.import_module("models.revision.model").ArticleRevision
revision_handler = importlib.import_module("api.revisions.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestArticleRevisionModel:
    def test_from_row(self):
        row = {
            "id": "r1",
            "article_id": "a1",
            "version_number": 3,
            "title": "Title v3",
            "content": "Body v3",
            "editor_id": "u1",
            "edit_type": "manual",
            "word_count": 100,
            "char_diff": 50,
            "created_at": "2026-01-01",
            "subtitle": "Sub",
            "cover_image_url": None,
            "reading_level": None,
            "tags_snapshot": '["python"]',
            "change_summary": "Fixes",
        }
        r = ArticleRevision.from_row(row)
        assert r.id == "r1"
        assert r.version_number == 3
        assert r.word_count == 100

    def test_to_dict_list_scope(self):
        r = ArticleRevision(
            id="r1",
            article_id="a1",
            version_number=1,
            title="T",
            content="C",
            editor_id="u1",
            edit_type="manual",
            word_count=10,
            char_diff=5,
            created_at="2026-01-01",
        )
        d = r.to_dict(scope="list")
        assert "content" not in d
        assert d["title"] == "T"

    def test_to_dict_detail_scope(self):
        r = ArticleRevision(
            id="r1",
            article_id="a1",
            version_number=1,
            title="T",
            content="Full body",
            editor_id="u1",
            edit_type="manual",
            word_count=10,
            char_diff=5,
            created_at="2026-01-01",
            subtitle="Sub",
        )
        d = r.to_dict(scope="detail")
        assert d["content"] == "Full body"
        assert d["subtitle"] == "Sub"


# ── Fake Service ──
class FakeRevisionService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_revisions(self, article_id, page=1, limit=20):
        self.calls.append(("list_revisions", article_id))
        return {
            "revisions": [{"id": "r1", "version_number": 1, "title": "Draft"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def get_revision(self, article_id, version_number):
        self.calls.append(("get_revision", article_id, version_number))
        if version_number == 999:
            raise ValueError("Revision not found")
        return {
            "id": "r1",
            "article_id": article_id,
            "version_number": version_number,
            "title": "Draft",
            "content": "Body text",
        }

    async def create_revision(self, **kwargs):
        self.calls.append(("create_revision", kwargs))
        return "new-r-id"


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


class RevisionClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def _dispatch(self, method, path, headers=None):
        parsed = urlparse(path)
        req = FakeRequest(method=method, url=path, headers=headers or {})
        svc = self.svc

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return svc

        orig = revision_handler.RevisionService
        revision_handler.RevisionService = _make_svc
        try:
            return asyncio.run(
                revision_handler.handle_revisions(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            revision_handler.RevisionService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeRevisionService(_Env())


@pytest.fixture
def client(svc):
    return RevisionClient(svc)


# ── Handler Tests ──
class TestRevisionHandler:
    def test_list_revisions(self, client, svc):
        resp = client.get(
            "/api/articles/a1/revisions",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "revisions" in data
        assert svc.calls[0] == ("list_revisions", "a1")

    def test_get_specific_revision(self, client, svc):
        resp = client.get(
            "/api/articles/a1/revisions/2",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["version_number"] == 2

    def test_get_missing_revision(self, client, svc):
        resp = client.get(
            "/api/articles/a1/revisions/999",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_unauth(self, client):
        resp = client.get("/api/articles/a1/revisions")
        assert resp.status_code == 401
