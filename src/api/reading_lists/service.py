from typing import Optional
from api.reading_lists.repository import ReadingListRepository
from utils.helpers import new_id, paginate


class ReadingListService:
    def __init__(self, env, ctx=None):
        self._repo = ReadingListRepository(env.DB, ctx)

    async def create_list(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        is_public: bool = False,
    ) -> str:
        if not name or not name.strip():
            raise ValueError("Name is required")
        lid = new_id()
        await self._repo.create_list(
            lid,
            user_id,
            name.strip(),
            description,
            cover_image_url,
            1 if is_public else 0,
        )
        return lid

    async def get_lists(self, user_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_lists_by_user(user_id, _limit, offset)
        total = await self._repo.count_lists_by_user(user_id)
        return {
            "reading_lists": [rl.to_dict() for rl in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def get_list_with_items(self, list_id: str, user_id: str):
        rl = await self._repo.find_list_by_id(list_id)
        if not rl:
            raise ValueError("Reading list not found")
        if not rl.is_public and rl.user_id != user_id:
            raise ValueError("Reading list not found")
        items = await self._repo.find_items_by_list(list_id)
        result = rl.to_dict()
        result["items"] = [item.to_dict() for item in items]
        return result

    async def update_list(
        self,
        list_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        is_public: bool = False,
    ) -> None:
        rl = await self._repo.find_list_by_id(list_id)
        if not rl or rl.user_id != user_id:
            raise ValueError("Reading list not found")
        await self._repo.update_list(
            list_id,
            user_id,
            name,
            description,
            cover_image_url,
            1 if is_public else 0,
        )

    async def delete_list(self, list_id: str, user_id: str) -> None:
        rl = await self._repo.find_list_by_id(list_id)
        if not rl or rl.user_id != user_id:
            raise ValueError("Reading list not found")
        if rl.is_default:
            raise ValueError("Cannot delete default reading list")
        await self._repo.delete_list(list_id, user_id)

    async def add_article(
        self,
        list_id: str,
        article_id: str,
        user_id: str,
        note: Optional[str] = None,
    ) -> str:
        rl = await self._repo.find_list_by_id(list_id)
        if not rl or rl.user_id != user_id:
            raise ValueError("Reading list not found")
        sort = await self._repo.max_sort_order(list_id) + 1
        iid = new_id()
        await self._repo.add_item(iid, list_id, article_id, note, sort)
        return iid

    async def remove_article(self, list_id: str, article_id: str, user_id: str) -> None:
        rl = await self._repo.find_list_by_id(list_id)
        if not rl or rl.user_id != user_id:
            raise ValueError("Reading list not found")
        await self._repo.remove_item(list_id, article_id)
