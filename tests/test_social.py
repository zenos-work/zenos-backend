"""
Phase 9 – Social endpoint tests.

Covers likes, bookmarks, follows, stats, and auth guards for /api/social/*.
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

create_token = importlib.import_module("auth.jwt_handler").create_token
social_handler = importlib.import_module("api.social.handler")
SocialActionResult = importlib.import_module("models.social.model").SocialActionResult

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


class DummyArticle:
    def __init__(self, id):
        self.id = id

    def to_dict(self):
        return {
            "id": self.id,
            "title": f"Article {self.id}",
            "slug": f"article-{self.id}",
            "status": "PUBLISHED",
            "author_id": "author-1",
            "views_count": 10,
            "likes_count": 2,
            "comments_count": 1,
            "is_featured": 0,
            "read_time_minutes": 3,
            "created_at": "2026-03-18T10:00:00Z",
            "tags": [],
        }


class DummyUser:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class FakeSocialService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def toggle_like(self, user_id, article_id, add):
        self.calls.append(("toggle_like", user_id, article_id, add))
        if article_id == "already-liked" and add:
            raise ValueError("Already liked")
        return SocialActionResult(action="like", target_id=article_id, active=add)

    async def check_liked(self, user_id, article_id):
        self.calls.append(("check_liked", user_id, article_id))
        if article_id == "missing":
            raise ValueError("Not found")
        return article_id == "liked"

    async def get_like_stats(self, article_id):
        self.calls.append(("get_like_stats", article_id))
        if article_id == "missing":
            raise ValueError("Not found")
        return {"article_id": article_id, "like_count": 7}

    async def get_bookmarks(self, user_id, page, limit):
        self.calls.append(("get_bookmarks", user_id, page, limit))
        return [DummyArticle("a1"), DummyArticle("a2")], 2

    async def toggle_bookmark(self, user_id, article_id, add):
        self.calls.append(("toggle_bookmark", user_id, article_id, add))
        if article_id == "already-bookmarked" and add:
            raise ValueError("Already bookmarked")
        return SocialActionResult(action="bookmark", target_id=article_id, active=add)

    async def check_bookmarked(self, user_id, article_id):
        self.calls.append(("check_bookmarked", user_id, article_id))
        if article_id == "missing":
            raise ValueError("Not found")
        return article_id == "bookmarked"

    async def toggle_follow(self, user_id, target_user_id, add):
        self.calls.append(("toggle_follow", user_id, target_user_id, add))
        if target_user_id == "already-followed" and add:
            raise ValueError("Already followed")
        return SocialActionResult(action="follow", target_id=target_user_id, active=add)

    async def check_following(self, user_id, target_user_id):
        self.calls.append(("check_following", user_id, target_user_id))
        if target_user_id == "missing":
            raise ValueError("Not found")
        return target_user_id == "followed"

    async def list_followers(self, user_id, page, limit):
        self.calls.append(("list_followers", user_id, page, limit))
        return [DummyUser("u1", "Follower One")], 1

    async def list_following(self, user_id, page, limit):
        self.calls.append(("list_following", user_id, page, limit))
        return [DummyUser("u2", "Following One")], 1

    async def get_user_social_stats(self, user_id):
        self.calls.append(("get_user_social_stats", user_id))
        if user_id == "missing":
            raise ValueError("Not found")
        return {"user_id": user_id, "followers_count": 5, "following_count": 3}


class SocialClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def delete(self, path, headers=None, json=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json)

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

        import api.social.handler as _h

        original = _h.SocialService
        _h.SocialService = _make_svc
        try:
            result = asyncio.run(
                social_handler.handle_social(
                    request,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            _h.SocialService = original
        return result


def _token(role="AUTHOR", sub="auth-user"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeSocialService(_Env())


@pytest.fixture
def client(svc):
    return SocialClient(svc)


@pytest.fixture
def author_token():
    return _token(role="AUTHOR", sub="auth-user")


class TestSocialEndpoints:
    def test_requires_auth_for_all_social_routes(self, client):
        r = client.get("/api/social/likes/a1/check")
        assert r.status_code == 401

    # ── Likes ─────────────────────────────────────────────────────────────────

    def test_like_article(self, client, author_token):
        r = client.post(
            "/api/social/likes/a1",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["action"]["action"] == "like"
        assert body["action"]["active"] is True

    def test_unlike_article(self, client, author_token):
        r = client.delete(
            "/api/social/likes/a1",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["action"]["active"] is False

    def test_like_conflict(self, client, author_token):
        r = client.post(
            "/api/social/likes/already-liked",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 409

    def test_like_check(self, client, author_token):
        r = client.get(
            "/api/social/likes/liked/check",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["has_liked"] is True

    def test_like_stats(self, client, author_token):
        r = client.get(
            "/api/social/likes/a1/stats",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["like_count"] == 7

    # ── Bookmarks ─────────────────────────────────────────────────────────────

    def test_list_bookmarks(self, client, author_token):
        r = client.get(
            "/api/social/bookmarks?page=1&limit=10",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2

    def test_bookmark_article(self, client, author_token):
        r = client.post(
            "/api/social/bookmarks/a1",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["action"]["action"] == "bookmark"

    def test_unbookmark_article(self, client, author_token):
        r = client.delete(
            "/api/social/bookmarks/a1",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["action"]["active"] is False

    def test_bookmark_check(self, client, author_token):
        r = client.get(
            "/api/social/bookmarks/bookmarked/check",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["has_bookmarked"] is True

    # ── Follows ───────────────────────────────────────────────────────────────

    def test_follow_user(self, client, author_token):
        r = client.post(
            "/api/social/follows/u2",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["action"]["action"] == "follow"

    def test_unfollow_user(self, client, author_token):
        r = client.delete(
            "/api/social/follows/u2",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["action"]["active"] is False

    def test_follow_check(self, client, author_token):
        r = client.get(
            "/api/social/follows/followed/check",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["is_following"] is True

    def test_followers_list(self, client, author_token):
        r = client.get(
            "/api/social/followers/auth-user?page=1&limit=10",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert data["pagination"]["total"] == 1

    def test_following_list(self, client, author_token):
        r = client.get(
            "/api/social/following/auth-user?page=1&limit=10",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert data["pagination"]["total"] == 1

    def test_follow_stats(self, client, author_token):
        r = client.get(
            "/api/social/stats/auth-user",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 200
        assert r.json()["followers_count"] == 5

    def test_unknown_route_returns_not_found(self, client, author_token):
        r = client.get(
            "/api/social/unknown/a1",
            headers={"Authorization": f"Bearer {author_token}"},
        )
        assert r.status_code == 404
