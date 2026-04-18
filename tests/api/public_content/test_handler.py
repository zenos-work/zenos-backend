import importlib

import pytest


public_handler = importlib.import_module("api.public_content.handler")
ArticleStatus = importlib.import_module("models.common.enums").ArticleStatus


class _Req:
    def __init__(self, method, path):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}


class _Ctx:
    pass


class _Env:
    pass


class _FakeResult:
    def to_dict(self):
        return {"items": [{"id": "a1"}], "page": 1, "limit": 20, "total": 1}


class _FakeArticle:
    def __init__(self, status=ArticleStatus.PUBLISHED):
        self.id = "a1"
        self.status = status

    def to_dict(self, _scope):
        return {"id": self.id, "status": self.status}


class _FakeArticleService:
    async def list_published(self, **_kwargs):
        return _FakeResult()

    async def get_by_id_or_slug(self, item_id):
        if item_id == "published":
            return _FakeArticle(ArticleStatus.PUBLISHED)
        if item_id == "draft":
            return _FakeArticle(ArticleStatus.DRAFT)
        return None


class _FakeTag:
    def __init__(self, name):
        self.name = name

    def to_dict(self):
        return {"name": self.name}


class _FakeTagService:
    async def list_all(self):
        return [_FakeTag("python"), _FakeTag("ai")]


@pytest.fixture(autouse=True)
def _patch_services(monkeypatch):
    monkeypatch.setattr(
        public_handler, "ArticleService", lambda env, ctx: _FakeArticleService()
    )
    monkeypatch.setattr(
        public_handler, "TagService", lambda env, ctx: _FakeTagService()
    )


class TestPublicContentHandler:
    @pytest.mark.asyncio
    async def test_health(self):
        res = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/health"),
            _Env(),
            "/api/public/v1/health",
            "GET",
            {},
            _Ctx(),
        )
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_list_articles(self):
        res = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/articles"),
            _Env(),
            "/api/public/v1/articles",
            "GET",
            {"page": ["1"], "limit": ["20"]},
            _Ctx(),
        )
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_get_article_detail_published(self):
        res = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/articles/published"),
            _Env(),
            "/api/public/v1/articles/published",
            "GET",
            {},
            _Ctx(),
        )
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_get_article_detail_not_found_or_unpublished(self):
        missing = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/articles/missing"),
            _Env(),
            "/api/public/v1/articles/missing",
            "GET",
            {},
            _Ctx(),
        )
        assert missing.status_code == 404

        draft = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/articles/draft"),
            _Env(),
            "/api/public/v1/articles/draft",
            "GET",
            {},
            _Ctx(),
        )
        assert draft.status_code == 404

    @pytest.mark.asyncio
    async def test_list_tags(self):
        res = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/tags"),
            _Env(),
            "/api/public/v1/tags",
            "GET",
            {},
            _Ctx(),
        )
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_not_found_path(self):
        res = await public_handler.handle_public_content(
            _Req("GET", "/api/public/v1/unknown"),
            _Env(),
            "/api/public/v1/unknown",
            "GET",
            {},
            _Ctx(),
        )
        assert res.status_code == 404
