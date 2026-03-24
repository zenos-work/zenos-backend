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

    async def list_onboarding(self) -> list:
        return await self._repo.find_onboarding_with_count()

    async def get_by_slug_or_id(self, identifier: str) -> Optional[Tag]:
        return await self._repo.find_by_slug_or_id(identifier)

    async def create(self, req: TagCreateRequest) -> Tag:
        tid = new_id()
        slug = slugify(req.name)
        category_slug = slugify(req.category_slug) if req.category_slug else None
        await self._repo.insert(
            tid,
            req.name,
            slug,
            req.tag_type,
            category_slug,
            req.is_onboarding_category,
        )
        return Tag(
            id=tid,
            name=req.name,
            slug=slug,
            tag_type=req.tag_type,
            category_slug=category_slug,
            is_onboarding_category=req.is_onboarding_category,
        )
