from typing import Optional
from api.tags.repository import TagRepository
from models.tag.model import Tag
from models.tag.requests import TagCreateRequest
from utils.helpers import new_id, slugify


class TagService:
    """Business logic for tags. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = TagRepository(env.DB, ctx)

    async def list_all(self) -> list:
        return await self._repo.find_all_with_count()

    async def get_by_slug_or_id(self, identifier: str) -> Optional[Tag]:
        return await self._repo.find_by_slug_or_id(identifier)

    async def create(self, req: TagCreateRequest) -> Tag:
        tid = new_id()
        slug = slugify(req.name)
        await self._repo.insert(tid, req.name, slug)
        return Tag(id=tid, name=req.name, slug=slug)
