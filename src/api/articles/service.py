from typing import Optional
from api.articles.repository import ArticleRepository
from models.article.model import Article
from models.article.requests import ArticleCreateRequest, ArticleUpdateRequest
from models.common.pagination import PaginatedResponse
from models.common.enums import ArticleStatus
from utils.helpers import new_id, unique_slug, calc_read_time


class ArticleService:
    """
    Business logic for articles.
    Zero SQL — all DB access goes through ArticleRepository.
    """

    def __init__(self, env, ctx=None):
        self._repo = ArticleRepository(env.DB, ctx)
        self._ctx = ctx

    async def _log(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    async def _analytics(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.analytics(name, data=data)

    async def list_published(
        self,
        page: int,
        limit: int,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse:
        """List published articles with optional tag/search filters."""
        return await self._repo.find_published(page, limit, tag, search)

    async def list_by_author(
        self,
        author_id: str,
        page: int,
        limit: int,
        status: Optional[str] = None,
    ) -> PaginatedResponse:
        """List articles by author (all statuses visible to author, PUBLISHED only to others)."""
        return await self._repo.find_by_author(author_id, page, limit, status)

    async def get_by_id_or_slug(self, identifier: str) -> Optional[Article]:
        return await self._repo.find_by_id_or_slug(identifier)

    async def get_owner(self, article_id: str) -> Optional[str]:
        return await self._repo.find_author_id(article_id)

    async def create(
        self,
        req: ArticleCreateRequest,
        author_id: str,
    ) -> Article:
        aid = new_id()
        slug = unique_slug(req.title)
        article = await self._repo.insert(
            aid,
            author_id,
            req.title,
            slug,
            req.subtitle,
            req.content,
            req.cover_image_url,
            calc_read_time(req.content),
            ArticleStatus.DRAFT,
        )
        if req.tag_ids:
            await self._repo.sync_tags(aid, req.tag_ids)
            article.tags = await self._repo._fetch_tags(aid)
        await self._log(
            "article.created",
            {
                "article_id": aid,
                "author_id": author_id,
                "title": req.title,
            },
        )
        return article

    async def update(
        self,
        article_id: str,
        req: ArticleUpdateRequest,
        current: Article,
    ) -> Article:
        title = req.title or current.title
        content = req.content or current.content
        article = await self._repo.update(
            article_id,
            title,
            content,
            req.subtitle or current.subtitle,
            req.cover_image_url or current.cover_image_url,
            calc_read_time(content),
        )
        if req.tag_ids is not None:
            await self._repo.sync_tags(article_id, req.tag_ids)
            article.tags = await self._repo._fetch_tags(article_id)
        return article

    async def delete(self, article_id: str) -> None:
        await self._repo.delete(article_id)
        await self._log("article.deleted", {"article_id": article_id})

    async def transition(
        self,
        article_id: str,
        new_status: str,
        actor_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> str:
        """Centralised status machine. All transition SQL lives in repository.set_status()."""
        s = ArticleStatus

        if new_status == s.SUBMITTED:
            await self._repo.set_status(article_id, s.SUBMITTED)
        elif new_status == s.APPROVED:
            await self._repo.set_status(article_id, s.APPROVED, approved_by=actor_id)
        elif new_status == s.REJECTED:
            await self._repo.set_status(article_id, s.REJECTED, rejection_note=note)
        elif new_status == s.PUBLISHED:
            await self._repo.set_status(article_id, s.PUBLISHED, publish=True)
        elif new_status == s.ARCHIVED:
            await self._repo.set_status(article_id, s.ARCHIVED)
        else:
            raise ValueError(f"Unknown status: {new_status}")

        _events = {
            s.SUBMITTED: "article.submitted",
            s.APPROVED: "article.approved",
            s.REJECTED: "article.rejected",
            s.PUBLISHED: "article.published",
            s.ARCHIVED: "article.archived",
        }
        await self._log(
            _events[new_status],
            {
                "article_id": article_id,
                "actor_id": actor_id,
            },
        )
        return new_status

    async def increment_views(self, article_id: str) -> None:
        await self._repo.increment_views(article_id)
        await self._analytics("article.viewed", {"article_id": article_id})
