import json
from typing import Optional, Tuple, List
from api.users.repository import UserRepository
from models.user.model import User
from models.user.requests import UpdateProfileRequest, UpdateRoleRequest
from models.common.enums import UserRole, Scope
from models.base import row_get


class UserService:
    """Business logic for users. Zero SQL."""

    def __init__(self, env, ctx=None):
        self._repo = UserRepository(env.DB, ctx)
        self._ctx = ctx

    async def _log(self, name: str, data: dict = None) -> None:
        if self._ctx:
            await self._ctx.log.event(name, data=data)

    async def get_by_id(
        self, user_id: str, scope: str = Scope.PUBLIC
    ) -> Optional[User]:
        if scope == Scope.PRIVATE:
            return await self._repo.find_by_id(user_id)
        return await self._repo.find_public_by_id(user_id)

    async def list_all(
        self, limit: int = 20, offset: int = 0
    ) -> Tuple[List[dict], int]:
        """Return paginated list of all users (name, avatar, role, created_at)."""
        users = await self._repo.find_all(limit=limit, offset=offset)
        total = await self._repo.count_all()
        data = [u.to_dict(Scope.PUBLIC) for u in users]
        return data, total

    async def update_profile(
        self, user_id: str, req: UpdateProfileRequest, skip_name_update: bool = False
    ) -> None:
        # For avatar-only updates, allow None name
        if skip_name_update:
            await self._repo.update_avatar_only(user_id, req.avatar_url)
        else:
            await self._repo.update_profile(user_id, req.name, req.avatar_url)

    async def self_upgrade_to_author(self, user_id: str) -> None:
        await self._repo.self_upgrade_role(user_id, UserRole.AUTHOR, UserRole.READER)
        await self._log(
            "user.role_changed",
            {
                "user_id": user_id,
                "new_role": UserRole.AUTHOR,
            },
        )

    async def set_role(self, user_id: str, req: UpdateRoleRequest) -> None:
        await self._repo.update_role(user_id, req.role)
        await self._log(
            "user.role_changed",
            {
                "user_id": user_id,
                "new_role": req.role,
            },
        )

    async def ban(self, user_id: str) -> None:
        await self._repo.ban(user_id)
        await self._log("user.banned", {"user_id": user_id})

    async def unban(self, user_id: str) -> None:
        await self._repo.unban(user_id)
        await self._log("user.unbanned", {"user_id": user_id})

    async def get_prefs(self, user_id: str) -> dict:
        await self._repo.ensure_prefs(user_id)
        row = await self._repo.find_prefs(user_id)
        topics_raw = row_get(row, "topics", "[]")
        try:
            topics = (
                json.loads(topics_raw) if isinstance(topics_raw, str) else topics_raw
            )
        except Exception:
            topics = []
        return {
            "topics": topics,
            "email_notifs": row_get(row, "notifications_enabled", 1),
            "theme": row_get(row, "theme", "dark"),
        }

    async def update_prefs(
        self,
        user_id: str,
        topics: list,
        email_notifs: int,
        theme: str,
    ) -> None:
        await self._repo.ensure_prefs(user_id)
        await self._repo.update_prefs(user_id, json.dumps(topics), email_notifs, theme)
