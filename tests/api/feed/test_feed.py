import pytest
import importlib

FeedService = importlib.import_module("api.feed.service").FeedService


class DummyRepo:
    def __init__(self):
        self.recommended = []
        self.topic_articles = []
        self.latest = []
        self.following = []
        self.trending = []
        self.recommended_total = 0
        self.topics_total = 0
        self.latest_total = 0
        self.following_total = 0
        self.trending_total = 0

    async def find_recommended(self, user_id, topics, limit, offset):
        return self.recommended

    async def count_recommended(self, user_id, topics):
        return self.recommended_total

    async def find_by_topics(self, topics, limit, offset):
        return self.topic_articles

    async def count_by_topics(self, topics):
        return self.topics_total

    async def find_latest(self, limit, offset):
        return self.latest

    async def count_latest(self):
        return self.latest_total

    async def find_following(self, user_id, limit, offset):
        return self.following

    async def count_following(self, user_id):
        return self.following_total

    async def find_trending(self, limit, offset):
        return self.trending

    async def count_trending(self):
        return self.trending_total


class DummyCtx:
    class _Log:
        async def analytics(self, name, data=None):
            return None

    log = _Log()


class DummyEnv:
    DB = None


@pytest.mark.asyncio
async def test_home_prefers_recommended_when_available():
    svc = FeedService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.recommended = ["a1", "a2"]
    repo.recommended_total = 23
    repo.latest = ["latest1"]
    repo.latest_total = 100
    svc._repo = repo

    result = await svc.home(page=1, user_id="u1", topics=["fintech"])

    assert result["feed"] == "personalised"
    assert result["articles"] == ["a1", "a2"]
    assert result["has_more"] is True


@pytest.mark.asyncio
async def test_home_falls_back_to_latest_when_no_signals():
    svc = FeedService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.latest = ["latest1", "latest2"]
    repo.latest_total = 2
    svc._repo = repo

    result = await svc.home(page=1, user_id="u1", topics=[])

    assert result["feed"] == "latest"
    assert result["articles"] == ["latest1", "latest2"]
    assert result["has_more"] is False


@pytest.mark.asyncio
async def test_following_includes_has_more():
    svc = FeedService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.following = ["a1"]
    repo.following_total = 45
    svc._repo = repo

    result = await svc.following(user_id="u1", page=1)

    assert result["feed"] == "following"
    assert result["has_more"] is True


@pytest.mark.asyncio
async def test_trending_returns_paginated_result():
    svc = FeedService(DummyEnv(), DummyCtx())
    repo = DummyRepo()
    repo.trending = ["t1", "t2"]
    repo.trending_total = 2
    svc._repo = repo

    result = await svc.trending(page=1)

    assert result["feed"] == "trending"
    assert result["articles"] == ["t1", "t2"]
    assert result["has_more"] is False
