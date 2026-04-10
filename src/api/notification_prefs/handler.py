"""Phase 10 Step 36 — Notification preferences + push handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.notification_prefs.service import NotificationPrefService


async def handle_notification_prefs(request, env, path, method, query, ctx):
    svc = NotificationPrefService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Push subscriptions ───────────────────────────────────
    # /api/notification-prefs/push[/:sid]
    if len(parts) >= 4 and parts[3] == "push":
        if method == "GET" and len(parts) == 4:
            return json_resp({"subscriptions": await svc.list_push_subs(uid)})
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            result = await svc.subscribe(
                user_id=uid,
                platform=data.get("platform", "web"),
                endpoint=data.get("endpoint", ""),
                p256dh_key=data.get("p256dh_key", ""),
                auth_key=data.get("auth_key", ""),
                device_name=data.get("device_name", ""),
            )
            return json_resp(result, 201)
        if method == "DELETE" and len(parts) == 5:
            try:
                return json_resp(await svc.unsubscribe(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Preferences ──────────────────────────────────────────
    # GET /api/notification-prefs
    if method == "GET" and len(parts) == 3:
        return json_resp({"preferences": await svc.list_prefs(uid)})

    # PUT /api/notification-prefs  (bulk upsert)
    if method == "PUT" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        prefs = data.get("preferences", [])
        result = await svc.bulk_upsert_prefs(uid, prefs)
        return json_resp({"updated": len(result)})

    # POST /api/notification-prefs  (single upsert)
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        result = await svc.upsert_pref(
            user_id=uid,
            notification_type=data.get("notification_type", ""),
            channel=data.get("channel", "in_app"),
            is_enabled=data.get("is_enabled", True),
        )
        return json_resp(result, 201)

    return error("Not found", 404)
