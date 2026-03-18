import json
from db.repository import BaseRepository
from api.feed import queries as Q
from models.article.model import Article
from models.base import row_get


class FeedRepository(BaseRepository):
    """Handles all database operations for feed queries."""

    @staticmethod
    def _extract_count(row) -> int:
        if not row:
            return 0
        return int(row_get(row, "c", 0) or 0)

    async def find_latest(self, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_FEED_LATEST, "PUBLISHED", limit, offset)
        return self.map_many(rows, Article)

    async def count_latest(self) -> int:
        row = await self.find_one(Q.COUNT_FEED_LATEST, "PUBLISHED")
        return self._extract_count(row)

    async def find_by_topics(self, topics: list, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_FEED_BY_TOPICS,
            "PUBLISHED",
            json.dumps(topics),
            limit,
            offset,
        )
        return self.map_many(rows, Article)

    async def count_by_topics(self, topics: list) -> int:
        row = await self.find_one(
            Q.COUNT_FEED_BY_TOPICS,
            "PUBLISHED",
            json.dumps(topics),
        )
        return self._extract_count(row)

    async def find_recommended(
        self, user_id: str, topics: list, limit: int, offset: int
    ) -> list:
        topics_json = json.dumps(topics or [])
        rows = await self.find_all(
            Q.SELECT_FEED_RECOMMENDED,
            topics_json,
            user_id,
            user_id,
            user_id,
            "PUBLISHED",
            limit,
            offset,
        )
        return self.map_many(rows, Article)

    async def count_recommended(self, user_id: str, topics: list) -> int:
        topics_json = json.dumps(topics or [])
        row = await self.find_one(
            Q.COUNT_FEED_RECOMMENDED,
            topics_json,
            user_id,
            user_id,
            user_id,
            "PUBLISHED",
        )
        return self._extract_count(row)

    async def find_following(self, user_id: str, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_FEED_FOLLOWING, user_id, "PUBLISHED", limit, offset
        )
        return self.map_many(rows, Article)

    async def count_following(self, user_id: str) -> int:
        row = await self.find_one(Q.COUNT_FEED_FOLLOWING, user_id, "PUBLISHED")
        return self._extract_count(row)

    async def find_featured(self) -> list:
        rows = await self.find_all(Q.SELECT_FEED_FEATURED, "PUBLISHED")
        return self.map_many(rows, Article)

    async def find_trending(self, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_FEED_TRENDING, "PUBLISHED", limit, offset)
        return self.map_many(rows, Article)

    async def count_trending(self) -> int:
        row = await self.find_one(Q.COUNT_FEED_TRENDING, "PUBLISHED")
        return self._extract_count(row)
