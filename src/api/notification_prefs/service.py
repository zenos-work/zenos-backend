"""Phase 10 Step 36 — Notification preference service."""

from api.notification_prefs.repository import NotificationPrefRepository
from utils.helpers import new_id


class NotificationPrefService:
    def __init__(self, env, ctx=None):
        self._repo = NotificationPrefRepository(env.DB, ctx)

    # ── Preferences ──────────────────────────────────────────
    async def list_prefs(self, user_id):
        items = await self._repo.list_prefs(user_id)
        return [p.to_dict() for p in items]

    async def upsert_pref(self, user_id, notification_type, channel, is_enabled=True):
        await self._repo.upsert_pref(user_id, notification_type, channel, is_enabled)
        return {
            "notification_type": notification_type,
            "channel": channel,
            "is_enabled": is_enabled,
        }

    async def bulk_upsert_prefs(self, user_id, prefs):
        results = []
        for p in prefs:
            await self._repo.upsert_pref(
                user_id, p["notification_type"], p["channel"], p.get("is_enabled", True)
            )
            results.append(p)
        return results

    async def delete_pref(self, user_id, notification_type, channel):
        await self._repo.delete_pref(user_id, notification_type, channel)

    # ── Push Subscriptions ───────────────────────────────────
    async def list_push_subs(self, user_id):
        items = await self._repo.list_push_subs(user_id)
        return [s.to_dict() for s in items]

    async def subscribe(
        self, user_id, platform, endpoint, p256dh_key, auth_key, device_name=""
    ):
        existing = await self._repo.get_push_sub_by_endpoint(user_id, endpoint)
        if existing:
            return {"id": existing.id, "already_subscribed": True}
        sid = new_id()
        await self._repo.create_push_sub(
            sid, user_id, platform, endpoint, p256dh_key, auth_key, device_name
        )
        return {"id": sid}

    async def unsubscribe(self, sid):
        existing = await self._repo.get_push_sub(sid)
        if not existing:
            raise ValueError("Subscription not found")
        await self._repo.deactivate_push_sub(sid)
        return {"id": sid, "deactivated": True}
