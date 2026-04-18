from typing import Optional
from api.blocks.repository import BlockRepository
from utils.helpers import paginate


class BlockService:
    def __init__(self, env, ctx=None):
        self._repo = BlockRepository(env.DB, ctx)

    async def block_user(
        self, blocker_id: str, blocked_id: str, reason: Optional[str] = None
    ) -> None:
        if blocker_id == blocked_id:
            raise ValueError("Cannot block yourself")
        already = await self._repo.is_blocked(blocker_id, blocked_id, "block")
        if already:
            raise ValueError("User already blocked")
        await self._repo.insert(blocker_id, blocked_id, "block", reason)

    async def unblock_user(self, blocker_id: str, blocked_id: str) -> None:
        await self._repo.delete(blocker_id, blocked_id, "block")

    async def mute_user(
        self, blocker_id: str, blocked_id: str, reason: Optional[str] = None
    ) -> None:
        if blocker_id == blocked_id:
            raise ValueError("Cannot mute yourself")
        already = await self._repo.is_blocked(blocker_id, blocked_id, "mute")
        if already:
            raise ValueError("User already muted")
        await self._repo.insert(blocker_id, blocked_id, "mute", reason)

    async def unmute_user(self, blocker_id: str, blocked_id: str) -> None:
        await self._repo.delete(blocker_id, blocked_id, "mute")

    async def list_blocked(self, user_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_by_blocker(user_id, "block", _limit, offset)
        total = await self._repo.count_by_blocker(user_id, "block")
        return {
            "data": [b.to_dict() for b in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def list_muted(self, user_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        items = await self._repo.find_by_blocker(user_id, "mute", _limit, offset)
        total = await self._repo.count_by_blocker(user_id, "mute")
        return {
            "data": [b.to_dict() for b in items],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }
