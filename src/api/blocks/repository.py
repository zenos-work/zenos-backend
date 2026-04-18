from typing import Optional, List
from db.repository import BaseRepository
from api.blocks import queries as Q
from models.block.model import UserBlock
from models.base import row_get


class BlockRepository(BaseRepository):
    async def insert(
        self,
        blocker_id: str,
        blocked_id: str,
        block_type: str = "block",
        reason: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.INSERT_BLOCK, blocker_id, blocked_id, block_type, reason or ""
        )

    async def delete(
        self, blocker_id: str, blocked_id: str, block_type: str = "block"
    ) -> None:
        await self.execute(Q.DELETE_BLOCK, blocker_id, blocked_id, block_type)

    async def find_by_blocker(
        self, blocker_id: str, block_type: str, limit: int, offset: int
    ) -> List[UserBlock]:
        rows = await self.find_all(
            Q.SELECT_BY_BLOCKER, blocker_id, block_type, limit, offset
        )
        return self.map_many(rows, UserBlock)

    async def count_by_blocker(self, blocker_id: str, block_type: str) -> int:
        row = await self.find_one(Q.COUNT_BY_BLOCKER, blocker_id, block_type)
        return row_get(row, "c", 0)

    async def is_blocked(
        self, blocker_id: str, blocked_id: str, block_type: str = "block"
    ) -> bool:
        row = await self.find_one(
            Q.SELECT_IS_BLOCKED, blocker_id, blocked_id, block_type
        )
        return row is not None

    async def get_blocked_ids(self, blocker_id: str) -> set:
        rows = await self.find_all(Q.SELECT_BLOCKED_IDS, blocker_id)
        return {row_get(r, "blocked_id") for r in rows if row_get(r, "blocked_id")}
