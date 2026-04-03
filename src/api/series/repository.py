from typing import Optional, List
from db.repository import BaseRepository
from api.series import queries as Q
from models.series import Series, ArticleSeriesInfo
from models.article.model import Article
from models.common.pagination import PaginatedResponse
from models.base import row_get


class SeriesRepository(BaseRepository):
    """
    Handles all database operations for series.
    Executes SQL from queries.py and maps rows to Series/ArticleSeriesInfo models.
    """

    # ── Read ──────────────────────────────────────────────

    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)
        self._series_schema_ready: Optional[bool] = None

    @staticmethod
    def _is_missing_series_table_error(exc: Exception) -> bool:
        message = str(exc).lower()
        return "no such table" in message and (
            "article_series" in message or "series" in message
        )

    async def _has_series_schema(self) -> bool:
        if self._series_schema_ready is not None:
            return self._series_schema_ready

        row = await self.find_one(
            """
            SELECT COUNT(1) AS table_count
            FROM sqlite_master
            WHERE type = 'table'
              AND name IN ('series', 'article_series')
            """
        )
        table_count = int(row_get(row, "table_count", 0) or 0)
        self._series_schema_ready = table_count >= 2
        return self._series_schema_ready

    async def find_by_id(self, series_id: str) -> Optional[Series]:
        row = await self.find_one(Q.SELECT_SERIES_BY_ID, series_id)
        return self.map_one(row, Series)

    async def find_by_author(
        self, author_id: str, page: int = 1, limit: int = 20
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        rows = await self.find_all(Q.SELECT_SERIES_BY_AUTHOR, author_id, limit, offset)
        series_list = self.map_many(rows, Series)

        # Get total count
        count_row = await self.find_one(Q.SELECT_SERIES_BY_AUTHOR_COUNT, author_id)
        total = row_get(count_row, "total", 0)

        return PaginatedResponse(items=series_list, page=page, limit=limit, total=total)

    async def find_series_articles(self, series_id: str) -> List[Article]:
        """Get all articles in a series, ordered by part number."""
        rows = await self.find_all(Q.SELECT_SERIES_ARTICLES, series_id, series_id)
        return self.map_many(rows, Article)

    async def find_article_series(self, article_id: str) -> Optional[ArticleSeriesInfo]:
        """Get series info for an article (if article is part of a series)."""
        if not await self._has_series_schema():
            return None
        try:
            row = await self.find_one(Q.SELECT_ARTICLE_SERIES, article_id)
        except Exception as exc:
            if self._is_missing_series_table_error(exc):
                # Older/local DBs may not yet have series tables migrated.
                self._series_schema_ready = False
                return None
            raise
        return self.map_one(row, ArticleSeriesInfo)

    # ── Write ─────────────────────────────────────────────

    async def create(
        self,
        series_id: str,
        author_id: str,
        name: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        created_at: str = "",
        updated_at: str = "",
    ) -> None:
        await self.execute(
            Q.INSERT_SERIES,
            series_id,
            author_id,
            name,
            description,
            cover_image_url,
            created_at,
            updated_at,
        )

    async def update(
        self,
        series_id: str,
        author_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        updated_at: str = "",
    ) -> None:
        await self.execute(
            Q.UPDATE_SERIES,
            name,
            description,
            cover_image_url,
            updated_at,
            series_id,
            author_id,
        )

    async def assign_article(
        self,
        article_series_id: str,
        article_id: str,
        series_id: str,
        part_number: int,
        created_at: str = "",
        updated_at: str = "",
    ) -> None:
        """Assign an article to a series at a specific part number."""
        await self.execute(
            Q.INSERT_ARTICLE_SERIES,
            article_series_id,
            article_id,
            series_id,
            part_number,
            created_at,
            updated_at,
        )

    async def update_article_part(
        self,
        article_id: str,
        series_id: str,
        part_number: int,
        updated_at: str = "",
    ) -> None:
        """Update the part number of an article in a series."""
        await self.execute(
            Q.UPDATE_ARTICLE_SERIES_PART,
            part_number,
            updated_at,
            article_id,
            series_id,
        )

    async def remove_article(self, article_id: str, series_id: str) -> None:
        """Remove an article from a series."""
        await self.execute(Q.DELETE_ARTICLE_SERIES, article_id, series_id)

    async def delete(self, series_id: str, author_id: str) -> None:
        """Delete a series (cascade deletes all article assignments)."""
        await self.execute(Q.DELETE_SERIES, series_id, author_id)

    async def exists(self, series_id: str, author_id: str) -> bool:
        """Check if series exists for given author."""
        row = await self.find_one(Q.SELECT_SERIES_EXISTS, series_id, author_id)
        return row is not None

    async def article_series_exists(self, article_id: str, series_id: str) -> bool:
        """Check if article is already assigned to series."""
        row = await self.find_one(Q.SELECT_ARTICLE_SERIES_EXISTS, article_id, series_id)
        return row is not None
