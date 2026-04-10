from typing import Optional
from api.revisions.repository import RevisionRepository
from utils.helpers import new_id, paginate


class RevisionService:
    def __init__(self, env, ctx=None):
        self._repo = RevisionRepository(env.DB, ctx)

    async def list_revisions(self, article_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        revisions = await self._repo.find_by_article(article_id, _limit, offset)
        total = await self._repo.count_by_article(article_id)
        return {
            "revisions": [r.to_dict(scope="list") for r in revisions],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def get_revision(self, article_id: str, version_number: int):
        rev = await self._repo.find_by_version(article_id, version_number)
        if not rev:
            raise ValueError("Revision not found")
        return rev.to_dict(scope="detail")

    async def create_revision(
        self,
        article_id: str,
        title: str,
        content: str,
        editor_id: str,
        edit_type: str = "manual",
        word_count: int = 0,
        char_diff: int = 0,
        subtitle: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        reading_level: Optional[str] = None,
        tags_snapshot: str = "[]",
        change_summary: Optional[str] = None,
    ) -> str:
        version = await self._repo.latest_version(article_id) + 1
        rid = new_id()
        await self._repo.create(
            rid,
            article_id,
            version,
            title,
            content,
            editor_id,
            edit_type,
            word_count,
            char_diff,
            subtitle,
            cover_image_url,
            reading_level,
            tags_snapshot,
            change_summary,
        )
        return rid
