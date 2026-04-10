from typing import Optional, List
from db.repository import BaseRepository
from api.revisions import queries as Q
from models.revision.model import ArticleRevision
from models.base import row_get


class RevisionRepository(BaseRepository):
    async def find_by_article(
        self, article_id: str, limit: int, offset: int
    ) -> List[ArticleRevision]:
        rows = await self.find_all(Q.SELECT_BY_ARTICLE, article_id, limit, offset)
        return self.map_many(rows, ArticleRevision)

    async def count_by_article(self, article_id: str) -> int:
        row = await self.find_one(Q.COUNT_BY_ARTICLE, article_id)
        return row_get(row, "c", 0)

    async def find_by_version(
        self, article_id: str, version_number: int
    ) -> Optional[ArticleRevision]:
        row = await self.find_one(
            Q.SELECT_BY_ARTICLE_AND_VERSION, article_id, version_number
        )
        return self.map_one(row, ArticleRevision)

    async def latest_version(self, article_id: str) -> int:
        row = await self.find_one(Q.SELECT_LATEST_VERSION, article_id)
        return row_get(row, "v", 0) or 0

    async def create(
        self,
        revision_id: str,
        article_id: str,
        version_number: int,
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
    ) -> None:
        await self.execute(
            Q.INSERT_REVISION,
            revision_id,
            article_id,
            version_number,
            title,
            subtitle or "",
            content,
            cover_image_url or "",
            reading_level or "",
            tags_snapshot,
            editor_id,
            change_summary or "",
            edit_type,
            word_count,
            char_diff,
        )
