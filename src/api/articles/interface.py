from typing import Optional, Protocol
from models.article.model import Article
from models.article.requests import ArticleCreateRequest, ArticleUpdateRequest
from models.common.pagination import PaginatedResponse


class IArticleService(Protocol):
    """
    Contract for all article operations.
    Any implementation (D1, mock, test double) must satisfy this.
    """

    async def list_published(
        self,
        page: int,
        limit: int,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse: ...

    async def get_by_id_or_slug(self, identifier: str) -> Optional[Article]: ...

    async def get_owner(self, article_id: str) -> Optional[str]: ...

    async def create(self, req: ArticleCreateRequest, author_id: str) -> Article: ...

    async def update(
        self, article_id: str, req: ArticleUpdateRequest, current: Article
    ) -> Article: ...

    async def delete(self, article_id: str) -> None: ...

    async def transition(
        self,
        article_id: str,
        new_status: str,
        actor_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> str: ...

    async def increment_views(self, article_id: str) -> None: ...
