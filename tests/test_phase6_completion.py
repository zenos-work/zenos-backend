import importlib
import sys
import types
from pathlib import Path

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
            import json

            if isinstance(self._body, (dict, list)):
                return self._body
            return json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _ResponseInstance(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    js_stub.fetch = None
    sys.modules["js"] = js_stub


helpers = importlib.import_module("utils.helpers")
articles_handler = importlib.import_module("api.articles.handler")


class DummyEnv:
    FRONTEND_URL = "http://localhost:5173"


class DummyRequest:
    def __init__(self, method="GET", path="/", headers=None, body=None):
        self.method = method
        self.url = f"http://localhost:8787{path}"
        self.headers = headers or {}
        self._body = body or {}

    async def json(self):
        return self._body


def test_cors_headers_use_configured_frontend_origin():
    request = DummyRequest(headers={"Origin": "http://localhost:5173"})

    headers = helpers.cors_headers(env=DummyEnv(), request=request)

    assert headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    assert "PATCH" in headers["Access-Control-Allow-Methods"]


@pytest.mark.asyncio
async def test_submit_for_approval_alias_reuses_submit_transition(monkeypatch):
    article = types.SimpleNamespace(author_id="author-1", status="DRAFT")

    async def fake_get_user(_request, _env):
        return {"sub": "author-1", "role": "AUTHOR"}

    class FakeArticleService:
        def __init__(self, env, ctx):
            pass

        async def get_by_id_or_slug(self, identifier):
            assert identifier == "article-1"
            return article

        async def transition(self, article_id, new_status, actor_id=None, note=None):
            assert article_id == "article-1"
            assert new_status == "SUBMITTED"
            return "SUBMITTED"

    monkeypatch.setattr(articles_handler, "get_user", fake_get_user)
    monkeypatch.setattr(articles_handler, "ArticleService", FakeArticleService)

    response = await articles_handler.handle_articles(
        DummyRequest(method="POST", path="/api/articles/article-1/submit-for-approval"),
        DummyEnv(),
        "/api/articles/article-1/submit-for-approval",
        "POST",
        {},
        None,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"
