from typing import Optional
from api.feed.repository import FeedRepository
from utils.helpers import paginate


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
        limit, offset = paginate(page, 20)

        # Personalised feed if user has topic preferences
        if topics:
            articles = await self._repo.find_by_topics(topics, limit, offset)
            if articles:
                feed_type = "personalised"
                await self._analytics(
                    "feed.loaded",
                    {
                        "user_id": user_id,
                        "feed_type": feed_type,
                        "count": len(articles),
                    },
                )
                return {"articles": articles, "feed": feed_type, "page": page}

        # Fallback — latest published
        articles = await self._repo.find_latest(limit, offset)
        await self._analytics(
            "feed.loaded",
            {"user_id": user_id, "feed_type": "latest", "count": len(articles)},
        )
        return {"articles": articles, "feed": "latest", "page": page}

    async def featured(self) -> list:
        return await self._repo.find_featured()

    async def following(self, user_id: str, page: int = 1) -> dict:
        limit, offset = paginate(page, 20)
        articles = await self._repo.find_following(user_id, limit, offset)
        await self._analytics(
            "feed.loaded",
            {"user_id": user_id, "feed_type": "following", "count": len(articles)},
        )
        return {"articles": articles, "feed": "following", "page": page}
