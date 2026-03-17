import json
from db.repository import BaseRepository
from api.feed import queries as Q
from models.article.model import Article


class FeedRepository(BaseRepository):
    """Handles all database operations for feed queries."""

    async def find_latest(self, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_FEED_LATEST, "PUBLISHED", limit, offset)
        return self.map_many(rows, Article)

    async def find_by_topics(self, topics: list, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_FEED_BY_TOPICS,
            "PUBLISHED",
            json.dumps(topics),
            limit,
            offset,
        )
        return self.map_many(rows, Article)

    async def find_following(self, user_id: str, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_FEED_FOLLOWING, user_id, "PUBLISHED", limit, offset
        )
        return self.map_many(rows, Article)

    async def find_featured(self) -> list:
        rows = await self.find_all(Q.SELECT_FEED_FEATURED, "PUBLISHED")
        return self.map_many(rows, Article)
