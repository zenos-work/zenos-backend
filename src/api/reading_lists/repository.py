from typing import Optional, List
from db.repository import BaseRepository
from api.reading_lists import queries as Q
from models.reading_list.model import ReadingList, ReadingListItem
from models.base import row_get


class ReadingListRepository(BaseRepository):
    # ── Lists ──
    async def create_list(
        self,
        list_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        is_public: int = 0,
    ) -> None:
        await self.execute(
            Q.INSERT_LIST,
            list_id,
            user_id,
            name,
            description or "",
            cover_image_url or "",
            is_public,
        )

    async def find_lists_by_user(
        self, user_id: str, limit: int, offset: int
    ) -> List[ReadingList]:
        rows = await self.find_all(Q.SELECT_LISTS_BY_USER, user_id, limit, offset)
        return self.map_many(rows, ReadingList)

    async def count_lists_by_user(self, user_id: str) -> int:
        row = await self.find_one(Q.COUNT_LISTS_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def find_list_by_id(self, list_id: str) -> Optional[ReadingList]:
        row = await self.find_one(Q.SELECT_LIST_BY_ID, list_id)
        return self.map_one(row, ReadingList)

    async def update_list(
        self,
        list_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        is_public: int = 0,
    ) -> None:
        await self.execute(
            Q.UPDATE_LIST,
            name,
            description or "",
            cover_image_url or "",
            is_public,
            list_id,
            user_id,
        )

    async def delete_list(self, list_id: str, user_id: str) -> None:
        await self.execute(Q.DELETE_LIST, list_id, user_id)

    # ── Items ──
    async def add_item(
        self,
        item_id: str,
        list_id: str,
        article_id: str,
        note: Optional[str] = None,
        sort_order: int = 0,
    ) -> None:
        await self.execute(
            Q.INSERT_ITEM, item_id, list_id, article_id, note or "", sort_order
        )

    async def find_items_by_list(self, list_id: str) -> List[ReadingListItem]:
        rows = await self.find_all(Q.SELECT_ITEMS_BY_LIST, list_id)
        return self.map_many(rows, ReadingListItem)

    async def count_items_by_list(self, list_id: str) -> int:
        row = await self.find_one(Q.COUNT_ITEMS_BY_LIST, list_id)
        return row_get(row, "c", 0)

    async def remove_item(self, list_id: str, article_id: str) -> None:
        await self.execute(Q.DELETE_ITEM, list_id, article_id)

    async def max_sort_order(self, list_id: str) -> int:
        row = await self.find_one(Q.SELECT_MAX_SORT_ORDER, list_id)
        return row_get(row, "m", 0) or 0
