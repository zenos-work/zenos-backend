import importlib

import pytest


FeedService = importlib.import_module("api.feed.service").FeedService


class _Env:
    DB = None


class _Ctx:
    class _Log:
        async def analytics(self, *_args, **_kwargs):
            return None

    log = _Log()


class TestFeedServiceAdditional:
    @pytest.mark.asyncio
    async def test_home_uses_topic_fallback_when_recommended_empty(self):
        svc = FeedService(_Env(), _Ctx())

        class _Repo:
            async def find_recommended(self, user_id, topics, limit, offset):
                return []

            async def count_recommended(self, user_id, topics):
                return 0

            async def find_by_topics(self, topics, limit, offset):
                return ["topic-article"]

            async def count_by_topics(self, topics):
                return 12

            async def find_latest(self, limit, offset):
                return ["latest"]

            async def count_latest(self):
                return 1

        svc._repo = _Repo()

        result = await svc.home(page=1, user_id="u1", topics=["fintech"])

        assert result["feed"] == "personalised"
        assert result["articles"] == ["topic-article"]
        assert result["has_more"] is False

    @pytest.mark.asyncio
    async def test_featured_passthrough(self):
        svc = FeedService(_Env(), _Ctx())

        class _Repo:
            async def find_featured(self):
                return ["featured-1", "featured-2"]

        svc._repo = _Repo()

        assert await svc.featured() == ["featured-1", "featured-2"]
