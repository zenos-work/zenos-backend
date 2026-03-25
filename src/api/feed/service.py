from typing import Optional
from api.feed.repository import FeedRepository
from utils.helpers import paginate


PAGE_SIZE = 20


class FeedService:
    """Business logic for personalised feeds. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = FeedRepository(env.DB, ctx)
        self._ctx = ctx

    async def _analytics(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.analytics(name, data=data)

    async def home(
        self,
        page: int = 1,
        user_id: Optional[str] = None,
        topics: list = None,
    ) -> dict:
        limit, offset = paginate(page, PAGE_SIZE)
        topics = topics or []

        # First priority: recommendation mix based on preferences + behaviour + follows.
        if user_id and topics:
            articles = await self._repo.find_recommended(user_id, topics, limit, offset)
            if articles:
                total = await self._repo.count_recommended(user_id, topics)
                feed_type = "personalised"
                await self._analytics(
                    "feed.loaded",
                    {
                        "user_id": user_id,
                        "feed_type": feed_type,
                        "count": len(articles),
                    },
                )
                return {
                    "articles": articles,
                    "feed": feed_type,
                    "page": page,
                    "total": total,
                    "has_more": page * limit < total,
                }

        # Second priority: explicit preference topics.
        if topics:
            articles = await self._repo.find_by_topics(topics, limit, offset)
            if articles:
                total = await self._repo.count_by_topics(topics)
                feed_type = "personalised"
                await self._analytics(
                    "feed.loaded",
                    {
                        "user_id": user_id,
                        "feed_type": feed_type,
                        "count": len(articles),
                    },
                )
                return {
                    "articles": articles,
                    "feed": feed_type,
                    "page": page,
                    "total": total,
                    "has_more": page * limit < total,
                }

        # Fallback — latest published
        articles = await self._repo.find_latest(limit, offset)
        total = await self._repo.count_latest()
        await self._analytics(
            "feed.loaded",
            {"user_id": user_id, "feed_type": "latest", "count": len(articles)},
        )
        return {
            "articles": articles,
            "feed": "latest",
            "page": page,
            "total": total,
            "has_more": page * limit < total,
        }

    async def featured(self) -> list:
        return await self._repo.find_featured()

    async def following(self, user_id: str, page: int = 1) -> dict:
        limit, offset = paginate(page, PAGE_SIZE)
        articles = await self._repo.find_following(user_id, limit, offset)
        total = await self._repo.count_following(user_id)
        await self._analytics(
            "feed.loaded",
            {"user_id": user_id, "feed_type": "following", "count": len(articles)},
        )
        return {
            "articles": articles,
            "feed": "following",
            "page": page,
            "total": total,
            "has_more": page * limit < total,
        }

    async def trending(self, page: int = 1) -> dict:
        limit, offset = paginate(page, PAGE_SIZE)
        articles = await self._repo.find_trending(limit, offset)
        total = await self._repo.count_trending()
        await self._analytics(
            "feed.loaded",
            {"feed_type": "trending", "count": len(articles)},
        )
        return {
            "articles": articles,
            "feed": "trending",
            "page": page,
            "total": total,
            "has_more": page * limit < total,
        }
