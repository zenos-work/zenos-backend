"""Phase 10 Step 36 — Notification preference repository."""

from db.repository import BaseRepository
from api.notification_prefs import queries as Q
from models.notification_pref.model import NotificationPreference, PushSubscription


class NotificationPrefRepository(BaseRepository):
    def _one(self, cls, row):
        return self.map_one(row, cls)

    def _many(self, rows, cls):
        return self.map_many(rows, cls)

    # ── Preferences ──────────────────────────────────────────
    async def list_prefs(self, user_id):
        return self._many(
            await self.find_all(Q.LIST_PREFS, user_id), NotificationPreference
        )

    async def get_pref(self, user_id, notification_type, channel):
        return self._one(
            NotificationPreference,
            await self.find_one(Q.GET_PREF, user_id, notification_type, channel),
        )

    async def upsert_pref(self, user_id, notification_type, channel, is_enabled):
        await self.execute(
            Q.UPSERT_PREF, user_id, notification_type, channel, int(is_enabled)
        )

    async def delete_pref(self, user_id, notification_type, channel):
        await self.execute(Q.DELETE_PREF, user_id, notification_type, channel)

    # ── Push Subscriptions ───────────────────────────────────
    async def list_push_subs(self, user_id):
        return self._many(
            await self.find_all(Q.LIST_PUSH_SUBS, user_id), PushSubscription
        )

    async def get_push_sub(self, sid):
        return self._one(PushSubscription, await self.find_one(Q.GET_PUSH_SUB, sid))

    async def get_push_sub_by_endpoint(self, user_id, endpoint):
        return self._one(
            PushSubscription,
            await self.find_one(Q.GET_PUSH_SUB_BY_ENDPOINT, user_id, endpoint),
        )

    async def create_push_sub(
        self, sid, user_id, platform, endpoint, p256dh_key, auth_key, device_name
    ):
        await self.execute(
            Q.INSERT_PUSH_SUB,
            sid,
            user_id,
            platform,
            endpoint,
            p256dh_key,
            auth_key,
            device_name,
        )

    async def deactivate_push_sub(self, sid):
        await self.execute(Q.DEACTIVATE_PUSH_SUB, sid)

    async def delete_push_sub(self, sid):
        await self.execute(Q.DELETE_PUSH_SUB, sid)
