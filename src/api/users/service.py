import json
from typing import Optional, Tuple, List
from api.users.repository import UserRepository
from models.user.model import User
from models.user.requests import UpdateProfileRequest, UpdateRoleRequest
from models.common.enums import UserRole, Scope
from models.base import row_get
from utils.helpers import paginate


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
            "email_notifs": row_get(row, "email_notifs", 1),
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

    async def list_reading_history(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 30,
    ) -> dict:
        page = max(1, int(page or 1))
        limit = max(1, min(int(limit or 30), 100))
        _limit, offset = paginate(page, limit)
        rows = await self._repo.find_reading_history(user_id, _limit, offset)
        items = [
            {
                "id": row.get("article_id"),
                "article_id": row.get("article_id"),
                "slug": row.get("slug"),
                "title": row.get("title"),
                "subtitle": row.get("subtitle"),
                "author_name": row.get("author_name"),
                "cover_image_url": row.get("cover_image_url"),
                "read_time_minutes": row.get("read_time_minutes", 0),
                "progress": row.get("progress", 0),
                "last_read_at": row.get("last_read_at"),
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in rows
        ]
        total = await self._repo.count_reading_history(user_id)
        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit,
                "has_more": page * _limit < total,
            },
        }

    @staticmethod
    def _normalize_reading_history_payload(payload: dict) -> dict:
        data = payload if isinstance(payload, dict) else {}
        article_id = str(data.get("article_id") or "").strip()
        slug = str(data.get("slug") or "").strip()
        title = str(data.get("title") or "").strip()

        if not article_id:
            raise ValueError("article_id is required")
        if not slug:
            raise ValueError("slug is required")
        if not title:
            raise ValueError("title is required")

        try:
            read_time_minutes = int(data.get("read_time_minutes", 0) or 0)
        except Exception as exc:
            raise ValueError("read_time_minutes must be a number") from exc
        read_time_minutes = max(0, read_time_minutes)

        try:
            progress = int(round(float(data.get("progress", 0) or 0)))
        except Exception as exc:
            raise ValueError("progress must be a number") from exc
        progress = max(0, min(100, progress))

        last_read_at = str(data.get("last_read_at") or "").strip() or None

        return {
            "id": article_id,
            "article_id": article_id,
            "slug": slug,
            "title": title,
            "subtitle": str(data.get("subtitle") or "").strip() or None,
            "author_name": str(data.get("author_name") or "").strip() or None,
            "cover_image_url": str(data.get("cover_image_url") or "").strip() or None,
            "read_time_minutes": read_time_minutes,
            "progress": progress,
            "last_read_at": last_read_at,
        }

    async def upsert_reading_history_item(self, user_id: str, payload: dict) -> dict:
        item = self._normalize_reading_history_payload(payload)
        await self._repo.upsert_reading_history_item(
            user_id,
            item["article_id"],
            item["slug"],
            item["title"],
            item["subtitle"],
            item["author_name"],
            item["cover_image_url"],
            item["read_time_minutes"],
            item["progress"],
            item["last_read_at"],
        )
        return item

    async def remove_reading_history_item(self, user_id: str, article_id: str) -> None:
        target = str(article_id or "").strip()
        if not target:
            raise ValueError("article_id is required")
        await self._repo.delete_reading_history_item(user_id, target)

    async def clear_reading_history(self, user_id: str) -> None:
        await self._repo.clear_reading_history(user_id)
