import uuid
from datetime import datetime, timezone
from typing import Optional, List
from api.series.repository import SeriesRepository
from api.articles.service import ArticleService
from models.series import Series, ArticleSeriesInfo
from models.series.requests import (
    SeriesCreateRequest,
    SeriesUpdateRequest,
    ArticleSeriesAssignRequest,
)
from models.article.model import Article
from models.common.pagination import PaginatedResponse


class SeriesService:
    """Business logic for series management."""

    def __init__(self, env, ctx=None):
        self.env = env
        self.ctx = ctx
        db = getattr(env, "DB", None) or getattr(env, "d1", None)
        if db is None:
            raise AttributeError("DB")
        self.repo = SeriesRepository(db, ctx)
        self.article_service = ArticleService(env, ctx)

    # ── Read ──────────────────────────────────────────────

    async def get_by_id(self, series_id: str) -> Optional[Series]:
        """Get series by ID."""
        return await self.repo.find_by_id(series_id)

    async def list_by_author(
        self, author_id: str, page: int = 1, limit: int = 20
    ) -> PaginatedResponse:
        """List all series for an author."""
        return await self.repo.find_by_author(author_id, page, limit)

    async def list_series_articles(self, series_id: str) -> List[Article]:
        """Get all articles in a series, ordered by part number."""
        return await self.repo.find_series_articles(series_id)

    async def get_article_series(self, article_id: str) -> Optional[ArticleSeriesInfo]:
        """Get series info for an article (if it's part of a series)."""
        return await self.repo.find_article_series(article_id)

    # ── Write ─────────────────────────────────────────────

    async def create(self, author_id: str, req: SeriesCreateRequest) -> Series:
        """Create a new series."""
        series_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        await self.repo.create(
            series_id=series_id,
            author_id=author_id,
            name=req.name,
            description=req.description,
            cover_image_url=req.cover_image_url,
            created_at=now,
            updated_at=now,
        )

        return await self.get_by_id(series_id)

    async def update(
        self, series_id: str, author_id: str, req: SeriesUpdateRequest
    ) -> Optional[Series]:
        """Update a series (only author can update)."""
        # Verify ownership
        existing = await self.get_by_id(series_id)
        if not existing or existing.author_id != author_id:
            return None

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await self.repo.update(
            series_id=series_id,
            author_id=author_id,
            name=req.name if req.name is not None else existing.name,
            description=(
                req.description if req.description is not None else existing.description
            ),
            cover_image_url=(
                req.cover_image_url
                if req.cover_image_url is not None
                else existing.cover_image_url
            ),
            updated_at=now,
        )

        return await self.get_by_id(series_id)

    async def assign_article(
        self,
        article_id: str,
        series_id: str,
        author_id: str,
        req: ArticleSeriesAssignRequest,
    ) -> bool:
        """Assign an article to a series at a specific part number."""
        # Verify article exists and belongs to author
        article = await self.article_service.get_by_id(article_id)
        if not article or article.author_id != author_id:
            return False

        # Verify series exists and belongs to author
        series = await self.get_by_id(req.series_id)
        if not series or series.author_id != author_id:
            return False

        # Check if already assigned
        exists = await self.repo.article_series_exists(article_id, req.series_id)
        if exists:
            # Update part number instead
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            await self.repo.update_article_part(
                article_id, req.series_id, req.part_number, updated_at=now
            )
        else:
            # Create new assignment
            article_series_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            await self.repo.assign_article(
                article_series_id=article_series_id,
                article_id=article_id,
                series_id=req.series_id,
                part_number=req.part_number,
                created_at=now,
                updated_at=now,
            )

        return True

    async def remove_article(
        self, article_id: str, series_id: str, author_id: str
    ) -> bool:
        """Remove an article from a series."""
        # Verify ownership
        series = await self.get_by_id(series_id)
        if not series or series.author_id != author_id:
            return False

        await self.repo.remove_article(article_id, series_id)
        return True

    async def delete(self, series_id: str, author_id: str) -> bool:
        """Delete a series (cascade deletes all article assignments)."""
        # Verify ownership
        existing = await self.get_by_id(series_id)
        if not existing or existing.author_id != author_id:
            return False

        await self.repo.delete(series_id, author_id)
        return True
