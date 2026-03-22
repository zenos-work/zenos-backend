"""
Phase 9 – Tag tests.

Covers:
  - TagCreateRequest validation
  - Tag.from_row mapping
  - Tags endpoint routes
"""

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
    import json

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

TagCreateRequest = importlib.import_module("models.tag.requests").TagCreateRequest
Tag = importlib.import_module("models.tag.model").Tag
create_token = importlib.import_module("auth.jwt_handler").create_token
tags_handler = importlib.import_module("api.tags.handler")

_JWT_SECRET = "test-secret"


class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json_body = json_body

    async def json(self):
        return self._json_body if self._json_body is not None else {}


class FakeCtx:
    trace_id = "test-trace-id"

    class log:
        @staticmethod
        async def event(name, data=None):
            pass


class FakeTagService:
    def __init__(self, env, ctx=None):
        self.tags = {
            "t1": Tag(id="t1", name="Fintech", slug="fintech", article_count=3),
            "python": Tag(id="t2", name="Python", slug="python", article_count=7),
        }

    async def list_all(self):
        return list(self.tags.values())

    async def get_by_slug_or_id(self, identifier):
        if identifier in self.tags:
            return self.tags[identifier]
        for tag in self.tags.values():
            if tag.id == identifier:
                return tag
        return None

    async def create(self, req):
        tag = Tag(
            id="new-tag-id",
            name=req.name,
            slug=req.name.strip().lower().replace(" ", "-"),
            article_count=0,
        )
        self.tags[tag.slug] = tag
        return tag


class TagsClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        request = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )
        svc = self.svc

        class _Env:
            JWT_SECRET = "test-secret"

        def _make_svc(_env, _ctx=None):
            return svc

        import api.tags.handler as _h

        original = _h.TagService
        _h.TagService = _make_svc
        try:
            result = asyncio.run(
                tags_handler.handle_tags(
                    request,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            _h.TagService = original
        return result


def _token(role="AUTHOR", sub="auth-user"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


# ─────────────────────────────────────────────────────────────────────────────
# Validation/model tests
# ─────────────────────────────────────────────────────────────────────────────


class TestTagCreateRequest:
    def test_valid_name(self):
        req = TagCreateRequest.from_body({"name": "  Fintech  "})
        assert req.name == "Fintech"

    def test_missing_name(self):
        with pytest.raises(ValueError, match="required"):
            TagCreateRequest.from_body({})

    def test_empty_name(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            TagCreateRequest.from_body({"name": "   "})

    def test_name_too_long(self):
        with pytest.raises(ValueError, match="50"):
            TagCreateRequest.from_body({"name": "X" * 51})

    def test_hashtag_name_is_normalized(self):
        req = TagCreateRequest.from_body({"name": " #FinOps "})
        assert req.name == "FinOps"


class TestTagModel:
    def test_from_row_maps_fields(self):
        tag = Tag.from_row(
            {"id": "t9", "name": "AI", "slug": "ai", "article_count": 12}
        )
        assert tag.id == "t9"
        assert tag.slug == "ai"
        assert tag.article_count == 12

    def test_from_row_default_article_count(self):
        tag = Tag.from_row({"id": "t8", "name": "Cloud", "slug": "cloud"})
        assert tag.article_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint tests
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeTagService(_Env())


@pytest.fixture
def client(svc):
    return TagsClient(svc)


@pytest.fixture
def superadmin_token():
    return _token(role="SUPERADMIN", sub="superadmin-user")


@pytest.fixture
def author_token():
    return _token(role="AUTHOR", sub="auth-user")


class TestTagsEndpoints:
    def test_list_tags(self, client):
        r = client.get("/api/tags")
        assert r.status_code == 200
        data = r.json()
        assert "tags" in data
        assert len(data["tags"]) >= 2

    def test_get_tag_by_slug(self, client):
        r = client.get("/api/tags/python")
        assert r.status_code == 200
        assert r.json()["tag"]["slug"] == "python"

    def test_get_tag_not_found(self, client):
        r = client.get("/api/tags/missing")
        assert r.status_code == 404

    def test_create_tag_requires_auth(self, client):
        r = client.post("/api/tags", json={"name": "Payments"})
        assert r.status_code == 401

    def test_create_tag_requires_writable_role(self, client):
        reader_token = _token(role="READER", sub="reader-user")
        r = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {reader_token}"},
            json={"name": "Payments"},
        )
        assert r.status_code == 403

    def test_create_tag_author(self, client, author_token):
        r = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {author_token}"},
            json={"name": "Payments"},
        )
        assert r.status_code == 201
        assert r.json()["tag"]["slug"] == "payments"

    def test_create_tag_with_hashtag(self, client, superadmin_token):
        r = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={"name": "#Cloud"},
        )
        assert r.status_code == 201
        assert r.json()["tag"]["name"] == "Cloud"
        assert r.json()["tag"]["slug"] == "cloud"

    def test_create_tag_validation_error(self, client, superadmin_token):
        r = client.post(
            "/api/tags",
            headers={"Authorization": f"Bearer {superadmin_token}"},
            json={"name": ""},
        )
        assert r.status_code == 422
