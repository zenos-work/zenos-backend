from typing import Optional
from api.sessions.repository import SessionRepository
from utils.helpers import new_id, paginate


class SessionService:
    def __init__(self, env, ctx=None):
        self._repo = SessionRepository(env.DB, ctx)

    async def list_sessions(self, user_id: str, page: int = 1, limit: int = 20):
        _limit, offset = paginate(page, limit)
        sessions = await self._repo.find_by_user(user_id, _limit, offset)
        total = await self._repo.count_by_user(user_id)
        return {
            "sessions": [s.to_dict() for s in sessions],
            "pagination": {
                "page": page,
                "limit": _limit,
                "total": total,
                "pages": (total + _limit - 1) // _limit if _limit else 0,
            },
        }

    async def create_session(
        self,
        user_id: str,
        device_info: Optional[str] = None,
        ip_hash: Optional[str] = None,
        country_code: Optional[str] = None,
        login_method: str = "google_oauth",
        expires_at: Optional[str] = None,
    ) -> str:
        sid = new_id()
        await self._repo.create(
            sid, user_id, device_info, ip_hash, country_code, login_method, expires_at
        )
        return sid

    async def revoke_session(
        self, session_id: str, user_id: str, reason: str = "user_revoked"
    ) -> None:
        session = await self._repo.find_by_id(session_id, user_id)
        if not session:
            raise ValueError("Session not found")
        if session.is_revoked:
            raise ValueError("Session already revoked")
        await self._repo.revoke(session_id, user_id, reason)

    async def revoke_other_sessions(
        self, user_id: str, current_session_id: str
    ) -> None:
        await self._repo.revoke_all_except(user_id, current_session_id)

    async def touch_session(self, session_id: str) -> None:
        await self._repo.touch(session_id)
