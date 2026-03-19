import importlib
import json

import pytest

from models.article.model import Article


FeedRepository = importlib.import_module("api.feed.repository").FeedRepository
feed_handler = importlib.import_module("api.feed.handler")
Q = importlib.import_module("api.feed.queries")


def _article_row(id="a1"):
    return {
        "id": id,
        "title": "Title",
        "slug": f"slug-{id}",
        "status": "PUBLISHED",
        "author_id": "u1",
        "views_count": 1,
        "likes_count": 1,
        "comments_count": 1,
        "is_featured": 0,
        "read_time_minutes": 2,
        "created_at": "2026-01-01T00:00:00Z",
        "content": "x" * 80,
        "updated_at": "2026-01-01T00:00:00Z",
    }


class TestFeedRepository:
    @pytest.mark.asyncio
    async def test_extract_count_variants(self):
        assert FeedRepository._extract_count(None) == 0
        assert FeedRepository._extract_count({"c": 0}) == 0
        assert FeedRepository._extract_count({"c": "4"}) == 4

    @pytest.mark.asyncio
    async def test_all_query_methods(self):
        repo = FeedRepository.__new__(FeedRepository)
        calls = []

        async def _find_all(sql, *params):
            calls.append((sql, params))
            if sql in {
                Q.SELECT_FEED_LATEST,
                Q.SELECT_FEED_BY_TOPICS,
                Q.SELECT_FEED_RECOMMENDED,
                Q.SELECT_FEED_FOLLOWING,
                Q.SELECT_FEED_FEATURED,
                Q.SELECT_FEED_TRENDING,
            }:
                return [_article_row("a1")]
            return []

        async def _find_one(sql, *params):
            calls.append((sql, params))
            if sql in {
                Q.COUNT_FEED_LATEST,
                Q.COUNT_FEED_BY_TOPICS,
                Q.COUNT_FEED_RECOMMENDED,
                Q.COUNT_FEED_FOLLOWING,
                Q.COUNT_FEED_TRENDING,
            }:
                return {"c": 3}
            return None

        repo.find_all = _find_all
        repo.find_one = _find_one
        repo.map_many = lambda rows, model_cls: [model_cls.from_row(r) for r in rows]

        latest = await repo.find_latest(20, 0)
        by_topics = await repo.find_by_topics(["fintech"], 20, 0)
        recommended = await repo.find_recommended("u1", ["fintech"], 20, 0)
        following = await repo.find_following("u1", 20, 0)
        featured = await repo.find_featured()
        trending = await repo.find_trending(20, 0)

        assert all(
            isinstance(x[0], Article)
            for x in [latest, by_topics, recommended, following, featured, trending]
        )

        assert await repo.count_latest() == 3
        assert await repo.count_by_topics(["fintech"]) == 3
        assert await repo.count_recommended("u1", ["fintech"]) == 3
        assert await repo.count_following("u1") == 3
        assert await repo.count_trending() == 3

        # Spot-check JSON-encoded topic parameters passed into SQL wrappers.
        by_topics_call = [c for c in calls if c[0] == Q.SELECT_FEED_BY_TOPICS][0]
        assert json.loads(by_topics_call[1][1]) == ["fintech"]

        recommended_call = [c for c in calls if c[0] == Q.SELECT_FEED_RECOMMENDED][0]
        assert json.loads(recommended_call[1][0]) == ["fintech"]


class _Req:
    def __init__(self, method="GET", path="/api/feed", headers=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = headers or {}


class _Stmt:
    def __init__(self, row):
        self._row = row

    def bind(self, *_args):
        return self

    async def first(self):
        return self._row


class _DB:
    def __init__(self, row=None):
        self._row = row

    def prepare(self, _sql):
        return _Stmt(self._row)


class _Env:
    def __init__(self, row=None):
        self.DB = _DB(row=row)


class _Ctx:
    trace_id = "trace-1"


class _A:
    def __init__(self, id):
        self.id = id

    def to_dict(self, scope=None):
        return {"id": self.id}


class _Svc:
    def __init__(self):
        self.calls = []

    async def home(self, page, user_id=None, topics=None):
        self.calls.append(("home", page, user_id, topics))
        return {
            "articles": [_A("a1")],
            "feed": "latest",
            "page": page,
            "total": 1,
            "has_more": False,
        }

    async def featured(self):
        self.calls.append(("featured",))
        return [_A("f1")]

    async def following(self, user_id, page):
        self.calls.append(("following", user_id, page))
        return {
            "articles": [_A("fo1")],
            "feed": "following",
            "page": page,
            "total": 1,
            "has_more": False,
        }

    async def trending(self, page):
        self.calls.append(("trending", page))
        return {
            "articles": [_A("t1")],
            "feed": "trending",
            "page": page,
            "total": 1,
            "has_more": False,
        }


class TestFeedHandler:
    @pytest.mark.asyncio
    async def test_method_not_allowed(self, monkeypatch):
        monkeypatch.setattr(feed_handler, "FeedService", lambda env, ctx: _Svc())

        resp = await feed_handler.handle_feed(
            _Req(method="POST"), _Env(), "/api/feed", "POST", {}, _Ctx()
        )
        assert resp.status_code == 405

    @pytest.mark.asyncio
    async def test_home_anonymous_and_with_user_preferences(self, monkeypatch):
        svc = _Svc()
        monkeypatch.setattr(feed_handler, "FeedService", lambda env, ctx: svc)

        async def _no_user(_request, _env):
            return None

        monkeypatch.setattr(feed_handler, "get_user", _no_user)
        resp = await feed_handler.handle_feed(
            _Req(path="/api/feed?page=2"),
            _Env(),
            "/api/feed",
            "GET",
            {"page": ["2"]},
            _Ctx(),
        )
        assert resp.status_code == 200
        assert svc.calls[-1] == ("home", 2, None, [])

        async def _user(_request, _env):
            return {"sub": "u1", "role": "AUTHOR"}

        monkeypatch.setattr(feed_handler, "get_user", _user)
        resp2 = await feed_handler.handle_feed(
            _Req(path="/api/feed?page=1"),
            _Env(row={"topics": "not-json"}),
            "/api/feed",
            "GET",
            {"page": ["1"]},
            _Ctx(),
        )
        assert resp2.status_code == 200
        assert svc.calls[-1] == ("home", 1, "u1", [])

    @pytest.mark.asyncio
    async def test_featured_following_trending_and_not_found(self, monkeypatch):
        svc = _Svc()
        monkeypatch.setattr(feed_handler, "FeedService", lambda env, ctx: svc)

        async def _user(_request, _env):
            return {"sub": "u1", "role": "AUTHOR"}

        monkeypatch.setattr(feed_handler, "get_user", _user)

        featured = await feed_handler.handle_feed(
            _Req(path="/api/feed/featured"),
            _Env(),
            "/api/feed/featured",
            "GET",
            {},
            _Ctx(),
        )
        following = await feed_handler.handle_feed(
            _Req(path="/api/feed/following?page=3"),
            _Env(),
            "/api/feed/following",
            "GET",
            {"page": ["3"]},
            _Ctx(),
        )
        trending = await feed_handler.handle_feed(
            _Req(path="/api/feed/trending?page=4"),
            _Env(),
            "/api/feed/trending",
            "GET",
            {"page": ["4"]},
            _Ctx(),
        )

        assert featured.status_code == 200
        assert following.status_code == 200
        assert trending.status_code == 200

        async def _no_user(_request, _env):
            return None

        monkeypatch.setattr(feed_handler, "get_user", _no_user)
        unauth = await feed_handler.handle_feed(
            _Req(path="/api/feed/following"),
            _Env(),
            "/api/feed/following",
            "GET",
            {},
            _Ctx(),
        )
        assert unauth.status_code == 401

        unknown = await feed_handler.handle_feed(
            _Req(path="/api/feed/unknown"),
            _Env(),
            "/api/feed/unknown",
            "GET",
            {},
            _Ctx(),
        )
        assert unknown.status_code == 404
