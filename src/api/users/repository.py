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
        rows = (
            await self._db.prepare(
                "SELECT id, email, name, role, is_active, created_at, avatar_url"
                " FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?"
            )
            .bind(limit, offset)
            .all()
        )
        return [self.map_one(row, User) for row in rows]

    async def count_all(self) -> int:
        """Total count of users."""
        row = await self._db.prepare("SELECT COUNT(*) as cnt FROM users").first()
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
        await self.execute(Q.UPDATE_PROFILE, name, avatar_url, user_id)

    async def update_avatar_only(self, user_id: str, avatar_url: Optional[str]) -> None:
        """Update only avatar, preserve existing name."""
        await (
            self._db.prepare(
                'UPDATE users SET avatar_url = ?, updated_at = datetime("now")'
                " WHERE id = ?"
            )
            .bind(avatar_url, user_id)
            .run()
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

    async def ban(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_BAN, user_id)

    async def unban(self, user_id: str) -> None:
        await self.execute(Q.UPDATE_UNBAN, user_id)
