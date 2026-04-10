"""Phase 12 Step 48 — GDPR export service."""

from db.repository import BaseRepository
from utils.helpers import new_id


class ExportService(BaseRepository):
    INSERT_EXPORT_REQUEST = (
        "INSERT INTO data_export_requests"
        " (id, user_id, status, format, expires_at)"
        " VALUES (?, ?, 'pending', 'zip', datetime('now', '+7 days'))"
    )

    SELECT_EXPORT_REQUEST = (
        "SELECT * FROM data_export_requests WHERE id = ? AND user_id = ? LIMIT 1"
    )

    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)

    async def request_export(self, user_id: str) -> str:
        rid = new_id()
        await self.execute(self.INSERT_EXPORT_REQUEST, rid, user_id)
        return rid

    async def get_export(self, user_id: str, request_id: str):
        row = await self.find_one(self.SELECT_EXPORT_REQUEST, request_id, user_id)
        if not row:
            return None
        d = dict(row) if not isinstance(row, dict) else row
        return {
            "id": d.get("id", request_id),
            "status": d.get("status", "pending"),
            "download_url": d.get("download_url", ""),
            "expires_at": d.get("expires_at", ""),
        }
