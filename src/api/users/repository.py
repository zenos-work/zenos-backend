from typing import Optional, List
from db.repository import BaseRepository
from api.users import queries as Q
from models.user.model import User


class UserRepository(BaseRepository):
    """Handles all database operations for users."""

    async def find_by_id(self, user_id: str) -> Optional[User]:
        row = await self.find_one(Q.SELECT_BY_ID, user_id)
        return self.map_one(row, User)

    async def find_public_by_id(self, user_id: str) -> Optional[User]:
        row = await self.find_one(Q.SELECT_PUBLIC_BY_ID, user_id)
        return self.map_one(row, User)

    async def find_all(self, limit: int = 20, offset: int = 0) -> List[User]:
        """Paginated list of all users, ordered by creation date."""
        rows = await self._ex.all(
            "SELECT id, email, name, role, is_active, created_at, avatar_url"
            " FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            limit,
            offset,
        )
        return [self.map_one(row, User) for row in rows]

    async def count_all(self) -> int:
        """Total count of users."""
        row = await self._ex.first("SELECT COUNT(*) as cnt FROM users")
        try:
            from models.base import row_get

            return row_get(row, "cnt", 0)
        except Exception as e:
            print("Error fetching all users", e)
            return 0

    async def find_prefs(self, user_id: str):
        return await self.find_one(Q.SELECT_PREFS_BY_USER, user_id)

    async def ensure_prefs(self, user_id: str) -> None:
        """Create default preferences row if not exists."""
        await self.execute(Q.INSERT_PREFS, user_id)

    async def update_profile(
        self, user_id: str, name: str, avatar_url: Optional[str]
    ) -> None:
        await self.execute(Q.UPDATE_PROFILE, name, avatar_url or "", user_id)

    async def update_avatar_only(self, user_id: str, avatar_url: Optional[str]) -> None:
        """Update only avatar, preserve existing name."""
        await self.execute(
            "UPDATE users SET avatar_url = NULLIF(?, ''), updated_at = datetime(\"now\") WHERE id = ?",
            avatar_url or "",
            user_id,
        )

    async def update_role(self, user_id: str, role: str) -> None:
        await self.execute(Q.UPDATE_ROLE, role, user_id)

    async def self_upgrade_role(
        self, user_id: str, new_role: str, current_role: str
    ) -> None:
        await self.execute(Q.UPDATE_SELF_ROLE, new_role, user_id, current_role)

    async def update_prefs(
        self, user_id: str, topics: str, email_notifs: int, theme: str
    ) -> None:
        await self.execute(Q.UPDATE_PREFS, topics, email_notifs, theme, user_id)

    async def find_reading_history(
        self, user_id: str, limit: int, offset: int
    ) -> list[dict]:
        from models.base import row_get

        rows = await super().find_all(
            Q.SELECT_READING_HISTORY_BY_USER, user_id, limit, offset
        )
        return [
            {
                "user_id": row_get(row, "user_id"),
                "article_id": row_get(row, "article_id"),
                "slug": row_get(row, "slug"),
                "title": row_get(row, "title"),
                "subtitle": row_get(row, "subtitle"),
                "author_name": row_get(row, "author_name"),
                "cover_image_url": row_get(row, "cover_image_url"),
                "read_time_minutes": int(row_get(row, "read_time_minutes", 0) or 0),
                "progress": int(row_get(row, "progress", 0) or 0),
                "last_read_at": row_get(row, "last_read_at"),
                "created_at": row_get(row, "created_at"),
                "updated_at": row_get(row, "updated_at"),
            }
            for row in rows
        ]

    async def count_reading_history(self, user_id: str) -> int:
        from models.base import row_get

        row = await self.find_one(Q.COUNT_READING_HISTORY_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def upsert_reading_history_item(
        self,
        user_id: str,
        article_id: str,
        slug: str,
        title: str,
        subtitle: Optional[str],
        author_name: Optional[str],
        cover_image_url: Optional[str],
        read_time_minutes: int,
        progress: int,
        last_read_at: Optional[str],
    ) -> None:
        await self.execute(
            Q.UPSERT_READING_HISTORY_ITEM,
            user_id,
            article_id,
            slug,
            title,
            subtitle or "",
            author_name or "",
            cover_image_url or "",
            read_time_minutes,
            progress,
            last_read_at or "",
        )

    async def delete_reading_history_item(self, user_id: str, article_id: str) -> None:
        await self.execute(Q.DELETE_READING_HISTORY_ITEM, user_id, article_id)

    async def clear_reading_history(self, user_id: str) -> None:
        await self.execute(Q.DELETE_READING_HISTORY_BY_USER, user_id)

    async def ban(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_BAN, user_id)

    async def unban(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_UNBAN, user_id)
