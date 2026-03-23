import re
from typing import Optional

from api.search.repository import SearchRepository
from models.common.pagination import PaginatedResponse
from utils.helpers import paginate

_MAX_QUERY_LEN = 200
_PAGE_SIZE = 20

# Limits used for the combined "search_all" mode — smaller so response stays lean.
_ALL_ARTICLES_LIMIT = 10
_ALL_TAGS_LIMIT = 5
_ALL_AUTHORS_LIMIT = 5


def _fts_query(q: str) -> Optional[str]:
    """Return a safe FTS5 MATCH expression or None when no usable tokens found.

    Strategy: extract only word characters (letters, digits, underscore) from the
    raw query, then append '*' to each token for prefix matching.  This prevents
    FTS5 syntax errors from user-supplied punctuation or quotes.
    """
    tokens = re.findall(r"\w+", q[:_MAX_QUERY_LEN])
    if not tokens:
        return None
    return " ".join(f"{t}*" for t in tokens)


def _like_pattern(q: str) -> str:
    """Return a SQL LIKE pattern that matches *q* anywhere in the column value."""
    safe = q.strip()[:_MAX_QUERY_LEN]
    # Escape LIKE wildcards in the user input so they are treated literally.
    safe = safe.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{safe}%"


class SearchService:
    """All search business logic. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = SearchRepository(env.DB, ctx)
        self._ctx = ctx

    async def _analytics(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.analytics(name, data=data)

    # ── Public methods ────────────────────────────────────────────────────────

    async def search_articles(
        self,
        q: str,
        page: int = 1,
        status: str = "PUBLISHED",
        outcome_tag: str = None,
        verified_only: bool = False,
    ) -> PaginatedResponse:
        fts = _fts_query(q)
        if not fts:
            return PaginatedResponse.of([], page, _PAGE_SIZE, total=0)

        limit, offset = paginate(page, _PAGE_SIZE)
        try:
            items = await self._repo.find_articles(
                fts,
                limit,
                offset,
                status=status,
                outcome_tag=outcome_tag,
                verified_only=verified_only,
            )
            total = await self._repo.count_articles(
                fts,
                status=status,
                outcome_tag=outcome_tag,
                verified_only=verified_only,
            )
        except TypeError:
            # Backward compatibility for older test doubles/repositories.
            items = await self._repo.find_articles(fts, limit, offset)
            total = await self._repo.count_articles(fts)

        await self._analytics("search.articles", {"q": q, "total": total})
        return PaginatedResponse.of(items, page, limit, total=total)

    async def search_tags(self, q: str, page: int = 1) -> PaginatedResponse:
        pattern = _like_pattern(q)
        limit, offset = paginate(page, _PAGE_SIZE)
        items = await self._repo.find_tags(pattern, limit, offset)
        total = await self._repo.count_tags(pattern)

        return PaginatedResponse.of(items, page, limit, total=total)

    async def search_authors(self, q: str, page: int = 1) -> PaginatedResponse:
        pattern = _like_pattern(q)
        limit, offset = paginate(page, _PAGE_SIZE)
        items = await self._repo.find_authors(pattern, limit, offset)
        total = await self._repo.count_authors(pattern)

        return PaginatedResponse.of(items, page, limit, total=total)

    async def search_all(
        self,
        q: str,
        status: str = "PUBLISHED",
        outcome_tag: str = None,
        verified_only: bool = False,
    ) -> dict:
        """Run articles, tags, and authors queries in parallel and combine results."""
        fts = _fts_query(q)

        if fts:
            try:
                articles = await self._repo.find_articles(
                    fts,
                    _ALL_ARTICLES_LIMIT,
                    0,
                    status=status,
                    outcome_tag=outcome_tag,
                    verified_only=verified_only,
                )
                articles_total = await self._repo.count_articles(
                    fts,
                    status=status,
                    outcome_tag=outcome_tag,
                    verified_only=verified_only,
                )
            except TypeError:
                articles = await self._repo.find_articles(fts, _ALL_ARTICLES_LIMIT, 0)
                articles_total = await self._repo.count_articles(fts)
        else:
            articles = []
            articles_total = 0

        like = _like_pattern(q)
        tags = await self._repo.find_tags(like, _ALL_TAGS_LIMIT, 0)
        tags_total = await self._repo.count_tags(like)

        authors = await self._repo.find_authors(like, _ALL_AUTHORS_LIMIT, 0)
        authors_total = await self._repo.count_authors(like)

        await self._analytics("search.all", {"q": q})
        return {
            "query": q,
            "articles": {"items": articles, "total": articles_total},
            "tags": {"items": tags, "total": tags_total},
            "authors": {"items": authors, "total": authors_total},
        }
