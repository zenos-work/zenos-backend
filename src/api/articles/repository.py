from typing import Optional
from db.repository import BaseRepository
from api.articles import queries as Q
from models.article.model import Article
from models.tag.model import Tag
from models.common.pagination import PaginatedResponse


class ArticleRepository(BaseRepository):
    """
    Handles all database operations for articles.
    Executes SQL from queries.py and maps rows to Article models.
    Contains zero business logic.
    """

    # ── Read ──────────────────────────────────────────────

    async def find_published(
        self,
        page: int,
        limit: int,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse:
        offset = (page - 1) * limit
        if tag:
            rows = await self.find_all(
                Q.SELECT_PUBLISHED_BY_TAG,
                "PUBLISHED",
                tag,
                limit,
                offset,
            )
        elif search:
            rows = await self.find_all(
                Q.SELECT_PUBLISHED_SEARCH,
                "PUBLISHED",
                f"%{search}%",
                f"%{search}%",
                limit,
                offset,
            )
        else:
            rows = await self.find_all(
                Q.SELECT_PUBLISHED_LIST,
                "PUBLISHED",
                limit,
                offset,
            )
        articles = self.map_many(rows, Article)
        return PaginatedResponse.of(articles, page, limit)

    async def find_by_id_or_slug(self, identifier: str) -> Optional[Article]:
        row = await self.find_one(Q.SELECT_BY_ID_OR_SLUG, identifier, identifier)
        if not row:
            return None
        article = self.map_one(row, Article)
        article.tags = await self._fetch_tags(article.id)
        return article

    async def find_by_author(
        self,
        author_id: str,
        page: int,
        limit: int,
        status: Optional[str] = None,
    ) -> PaginatedResponse:
        """List articles by author. Optional status filter."""
        offset = (page - 1) * limit
        if status:
            rows = await self.find_all(
                Q.SELECT_BY_AUTHOR_AND_STATUS,
                author_id,
                status,
                limit,
                offset,
            )
        else:
            rows = await self.find_all(
                Q.SELECT_BY_AUTHOR,
                author_id,
                limit,
                offset,
            )
        articles = self.map_many(rows, Article)
        return PaginatedResponse.of(articles, page, limit)

    async def find_author_id(self, article_id: str) -> Optional[str]:
        from models.base import row_get

        row = await self.find_one(Q.SELECT_AUTHOR_ID_BY_ID, article_id)
        return row_get(row, "author_id") if row else None

    async def find_status_row(self, article_id: str):
        """Returns raw row with id, author_id, status — for transition checks."""
        return await self.find_one(Q.SELECT_STATUS_BY_ID, article_id)

    async def _fetch_tags(self, article_id: str) -> list:
        rows = await self.find_all(Q.SELECT_TAGS_FOR_ARTICLE, article_id)
        return self.map_many(rows, Tag)

    # ── Write ─────────────────────────────────────────────

    async def insert(
        self,
        aid: str,
        author_id: str,
        title: str,
        slug: str,
        subtitle: Optional[str],
        content: str,
        cover_image_url: Optional[str],
        read_time: int,
        status: str,
    ) -> Article:
        await self.execute(
            Q.INSERT_ARTICLE,
            aid,
            author_id,
            title,
            slug,
            subtitle,
            content,
            cover_image_url,
            read_time,
            status,
        )
        row = await self.find_one(Q.SELECT_BY_ID_OR_SLUG, aid, aid)
        article = self.map_one(row, Article)
        article.tags = await self._fetch_tags(aid)
        return article

    async def update(
        self,
        article_id: str,
        title: str,
        content: str,
        subtitle: Optional[str],
        cover_image_url: Optional[str],
        read_time: int,
    ) -> Article:
        await self.execute(
            Q.UPDATE_ARTICLE,
            title,
            content,
            subtitle,
            cover_image_url,
            read_time,
            article_id,
        )
        row = await self.find_one(Q.SELECT_BY_ID_OR_SLUG, article_id, article_id)
        article = self.map_one(row, Article)
        article.tags = await self._fetch_tags(article_id)
        return article

    async def delete(self, article_id: str) -> None:
        await self.execute(Q.DELETE_ARTICLE, article_id)

    async def set_status(
        self,
        article_id: str,
        status: str,
        approved_by: str = None,
        rejection_note: str = None,
        publish: bool = False,
    ) -> None:
        if approved_by:
            await self.execute(
                Q.UPDATE_APPROVE,
                status,
                approved_by,
                article_id,
                "SUBMITTED",
            )
        elif rejection_note:
            await self.execute(
                Q.UPDATE_REJECT,
                status,
                rejection_note,
                article_id,
            )
        elif publish:
            await self.execute(
                Q.UPDATE_PUBLISH,
                status,
                article_id,
                "APPROVED",
            )
        else:
            await self.execute(Q.UPDATE_STATUS, status, article_id)

    async def sync_tags(self, article_id: str, tag_ids: list) -> None:
        await self.execute(Q.DELETE_ARTICLE_TAGS, article_id)
        for tid in tag_ids:
            await self.execute(Q.INSERT_ARTICLE_TAG, article_id, tid)

    async def increment_views(self, article_id: str) -> None:
        await self.execute(Q.UPDATE_INCREMENT_VIEWS, article_id)

    async def increment_likes(self, article_id: str) -> None:
        await self.execute(Q.UPDATE_INCREMENT_LIKES, article_id)

    async def decrement_likes(self, article_id: str) -> None:
        await self.execute(Q.UPDATE_DECREMENT_LIKES, article_id)

    async def increment_comments(self, article_id: str) -> None:
        await self.execute(Q.UPDATE_INCREMENT_COMMENTS, article_id)
