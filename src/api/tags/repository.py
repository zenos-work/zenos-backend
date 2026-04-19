from typing import Optional
from db.repository import BaseRepository
from api.tags import queries as Q
from models.tag.model import Tag


class TagRepository(BaseRepository):
    """Handles all database operations for tags."""

    async def find_all_with_count(self) -> list:
        rows = await self.find_all(Q.SELECT_ALL_WITH_COUNT)
        return self.map_many(rows, Tag)

    async def find_onboarding_with_count(self) -> list:
        rows = await self.find_all(Q.SELECT_ONBOARDING_WITH_COUNT)
        return self.map_many(rows, Tag)

    async def find_by_slug_or_id(self, identifier: str) -> Optional[Tag]:
        row = await self.find_one(Q.SELECT_BY_SLUG_OR_ID, identifier, identifier)
        return self.map_one(row, Tag)

    async def insert(
        self,
        tid: str,
        name: str,
        slug: str,
        tag_type: str,
        category_slug: str,
        is_onboarding_category: int,
    ) -> None:
        await self.execute(
            Q.INSERT_TAG,
            tid,
            name,
            slug,
            tag_type,
            category_slug,
            is_onboarding_category,
        )
