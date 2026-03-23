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

    @staticmethod
    def _optional_text(value: Optional[str]) -> str:
        if value is None:
            return ""
        text = str(value).strip()
        return text

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
        last_verified_at: Optional[str],
        expires_at: Optional[str],
        seo_title: Optional[str],
        seo_description: Optional[str],
        canonical_url: Optional[str],
        og_image_url: Optional[str],
        seo_schema_type: Optional[str],
    ) -> Article:
        await self.execute(
            Q.INSERT_ARTICLE,
            aid,
            author_id,
            title,
            slug,
            self._optional_text(subtitle),
            content,
            self._optional_text(cover_image_url),
            read_time,
            status,
            self._optional_text(last_verified_at),
            self._optional_text(expires_at),
            self._optional_text(seo_title),
            self._optional_text(seo_description),
            self._optional_text(canonical_url),
            self._optional_text(og_image_url),
            self._optional_text(seo_schema_type or "Article"),
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
        last_verified_at: Optional[str],
        expires_at: Optional[str],
        seo_title: Optional[str],
        seo_description: Optional[str],
        canonical_url: Optional[str],
        og_image_url: Optional[str],
        seo_schema_type: Optional[str],
    ) -> Article:
        await self.execute(
            Q.UPDATE_ARTICLE,
            title,
            content,
            self._optional_text(subtitle),
            self._optional_text(cover_image_url),
            read_time,
            self._optional_text(last_verified_at),
            self._optional_text(expires_at),
            self._optional_text(seo_title),
            self._optional_text(seo_description),
            self._optional_text(canonical_url),
            self._optional_text(og_image_url),
            self._optional_text(seo_schema_type or "Article"),
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
        moderation_state: str = None,
        moderation_note: str = None,
        publish: bool = False,
    ) -> None:
        if approved_by:
            await self.execute(
                Q.UPDATE_APPROVE,
                status,
                approved_by,
                moderation_state or "APPROVED_BY_ADMIN",
                self._optional_text(moderation_note),
                article_id,
                "SUBMITTED",
            )
        elif rejection_note:
            await self.execute(
                Q.UPDATE_REJECT,
                status,
                rejection_note,
                moderation_state or "REJECTED_BY_ADMIN",
                self._optional_text(moderation_note),
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

    async def update_moderation_state(
        self,
        article_id: str,
        moderation_state: str,
        moderation_note: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.UPDATE_MODERATION_STATE,
            moderation_state,
            self._optional_text(moderation_note),
            article_id,
        )

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

    async def list_approver_ids(self) -> list[str]:
        from models.base import row_get

        rows = await self.find_all(Q.SELECT_APPROVER_IDS)
        return [row_get(r, "id") for r in rows if row_get(r, "id")]

    async def insert_notification(
        self,
        nid: str,
        user_id: str,
        actor_id: Optional[str],
        type_: str,
        article_id: Optional[str],
        message: str,
    ) -> None:
        await self.execute(
            Q.INSERT_NOTIFICATION,
            nid,
            user_id,
            actor_id,
            type_,
            article_id,
            None,
            message,
        )
