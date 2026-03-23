from db.repository import BaseRepository
from api.search import queries as Q
from models.article.model import Article
from models.tag.model import Tag
from models.user.model import User
from models.base import row_get


class SearchRepository(BaseRepository):
    """Handles all database operations for search queries. Zero business logic."""

    @staticmethod
    def _extract_count(row) -> int:
        if not row:
            return 0
        return int(row_get(row, "c", 0) or 0)

    # ── Articles FTS ──────────────────────────────────────────────────────────

    async def find_articles(
        self,
        fts_query: str,
        limit: int,
        offset: int,
        status: str = "PUBLISHED",
        outcome_tag: str = None,
        verified_only: bool = False,
    ) -> list:
        rows = await self.find_all(
            Q.SELECT_ARTICLES_FTS,
            fts_query,
            status,
            status,
            1 if verified_only else 0,
            outcome_tag,
            outcome_tag,
            limit,
            offset,
        )
        return self.map_many(rows, Article)

    async def count_articles(
        self,
        fts_query: str,
        status: str = "PUBLISHED",
        outcome_tag: str = None,
        verified_only: bool = False,
    ) -> int:
        row = await self.find_one(
            Q.COUNT_ARTICLES_FTS,
            fts_query,
            status,
            status,
            1 if verified_only else 0,
            outcome_tag,
            outcome_tag,
        )
        return self._extract_count(row)

    # ── Tags ──────────────────────────────────────────────────────────────────

    async def find_tags(self, like_pattern: str, limit: int, offset: int) -> list:
        rows = await self.find_all(
            Q.SELECT_TAGS_SEARCH, like_pattern, like_pattern, limit, offset
        )
        return self.map_many(rows, Tag)

    async def count_tags(self, like_pattern: str) -> int:
        row = await self.find_one(Q.COUNT_TAGS_SEARCH, like_pattern, like_pattern)
        return self._extract_count(row)

    # ── Authors ───────────────────────────────────────────────────────────────

    async def find_authors(self, like_pattern: str, limit: int, offset: int) -> list:
        rows = await self.find_all(Q.SELECT_AUTHORS_SEARCH, like_pattern, limit, offset)
        return self.map_many(rows, User)

    async def count_authors(self, like_pattern: str) -> int:
        row = await self.find_one(Q.COUNT_AUTHORS_SEARCH, like_pattern)
        return self._extract_count(row)
