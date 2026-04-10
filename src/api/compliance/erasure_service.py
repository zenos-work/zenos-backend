"""Phase 12 Step 48 — GDPR hard erasure service."""

from db.repository import BaseRepository
from utils.helpers import new_id


class ErasureService(BaseRepository):
    INSERT_ERASURE_REQUEST = (
        "INSERT INTO data_erasure_requests"
        " (id, user_id, status, execute_after, requested_by)"
        " VALUES (?, ?, 'pending', datetime('now', '+30 days'), ?)"
    )

    SELECT_PENDING_QUEUE = (
        "SELECT * FROM data_erasure_requests"
        " WHERE status = 'pending'"
        " ORDER BY execute_after ASC"
    )

    SELECT_ERASURE_REQUEST = (
        "SELECT * FROM data_erasure_requests" " WHERE id = ?" " LIMIT 1"
    )

    UPDATE_ERASURE_EXECUTED = (
        "UPDATE data_erasure_requests"
        " SET status = 'executed', executed_at = datetime('now'), executed_by = ?"
        " WHERE id = ?"
    )

    # Minimal anonymization + cleanup actions.
    ANONYMIZE_USER = (
        "UPDATE users"
        " SET name = 'Deleted User',"
        "     email = 'deleted+' || id || '@example.invalid',"
        "     bio = '',"
        "     profile_image_url = '',"
        "     cover_image_url = ''"
        " WHERE id = ?"
    )
    DELETE_SOCIAL = "DELETE FROM follows WHERE follower_id = ? OR following_id = ?"
    DELETE_ENGAGEMENT = "DELETE FROM likes WHERE user_id = ?"
    DELETE_BOOKMARKS = "DELETE FROM bookmarks WHERE user_id = ?"
    DELETE_READING_HISTORY = "DELETE FROM user_reading_history WHERE user_id = ?"
    DELETE_SESSIONS = "DELETE FROM user_sessions WHERE user_id = ?"
    DELETE_PUSH_SUBS = "DELETE FROM push_subscriptions WHERE user_id = ?"

    INSERT_AUDIT_LOG = (
        "INSERT INTO audit_log"
        " (id, org_id, actor_user_id, action, entity_type, entity_id, details)"
        " VALUES (?, '', ?, 'gdpr_erasure_executed', 'user', ?, ?)"
    )

    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)

    async def request_erasure(self, user_id: str, password_confirmed: bool) -> str:
        if not password_confirmed:
            raise ValueError("password confirmation is required")
        rid = new_id()
        await self.execute(self.INSERT_ERASURE_REQUEST, rid, user_id, user_id)
        return rid

    async def queue(self):
        rows = await self.find_all(self.SELECT_PENDING_QUEUE)
        return [dict(r) if not isinstance(r, dict) else r for r in rows]

    async def execute_erasure(self, request_id: str, actor_user_id: str):
        req = await self.find_one(self.SELECT_ERASURE_REQUEST, request_id)
        if not req:
            raise ValueError("Erasure request not found")
        req_d = dict(req) if not isinstance(req, dict) else req
        user_id = req_d.get("user_id", "")
        if not user_id:
            raise ValueError("Invalid erasure request")

        await self.execute(self.ANONYMIZE_USER, user_id)
        await self.execute(self.DELETE_SOCIAL, user_id, user_id)
        await self.execute(self.DELETE_ENGAGEMENT, user_id)
        await self.execute(self.DELETE_BOOKMARKS, user_id)
        await self.execute(self.DELETE_READING_HISTORY, user_id)
        await self.execute(self.DELETE_SESSIONS, user_id)
        await self.execute(self.DELETE_PUSH_SUBS, user_id)

        await self.execute(self.UPDATE_ERASURE_EXECUTED, actor_user_id, request_id)
        await self.execute(
            self.INSERT_AUDIT_LOG,
            new_id(),
            actor_user_id,
            user_id,
            '{"reason":"gdpr_erasure"}',
        )

        return {
            "id": request_id,
            "user_id": user_id,
            "status": "executed",
        }
