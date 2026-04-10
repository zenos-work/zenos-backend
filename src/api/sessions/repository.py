from typing import Optional, List
from db.repository import BaseRepository
from api.sessions import queries as Q
from models.session.model import UserSession


class SessionRepository(BaseRepository):
    async def find_by_user(
        self, user_id: str, limit: int, offset: int
    ) -> List[UserSession]:
        rows = await self.find_all(Q.SELECT_BY_USER, user_id, limit, offset)
        return self.map_many(rows, UserSession)

    async def count_by_user(self, user_id: str) -> int:
        from models.base import row_get

        row = await self.find_one(Q.COUNT_BY_USER, user_id)
        return row_get(row, "c", 0)

    async def find_by_id(self, session_id: str, user_id: str) -> Optional[UserSession]:
        row = await self.find_one(Q.SELECT_BY_ID, session_id, user_id)
        return self.map_one(row, UserSession)

    async def create(
        self,
        session_id: str,
        user_id: str,
        device_info: Optional[str] = None,
        ip_hash: Optional[str] = None,
        country_code: Optional[str] = None,
        login_method: str = "google_oauth",
        expires_at: Optional[str] = None,
    ) -> None:
        await self.execute(
            Q.INSERT_SESSION,
            session_id,
            user_id,
            device_info or "",
            ip_hash or "",
            country_code or "",
            login_method,
            expires_at or "",
        )

    async def revoke(
        self, session_id: str, user_id: str, reason: str = "user_revoked"
    ) -> None:
        await self.execute(Q.REVOKE_SESSION, reason, session_id, user_id)

    async def revoke_all_except(self, user_id: str, current_session_id: str) -> None:
        await self.execute(Q.REVOKE_ALL_SESSIONS, user_id, current_session_id)

    async def touch(self, session_id: str) -> None:
        await self.execute(Q.TOUCH_SESSION, session_id)
