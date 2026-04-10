"""Phase 10 Steps 39-40 — Usage alerts & quota handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.usage_alerts.service import UsageAlertService


async def handle_usage_alerts(request, env, path, method, query, ctx):
    svc = UsageAlertService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Quota check ──────────────────────────────────────────
    # GET /api/usage/quota?org_id=...&year_month=...
    if len(parts) == 4 and parts[3] == "quota" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        year_month = query.get("year_month", [""])[0]
        result = await svc.check_quota(org_id, year_month)
        if result.get("exceeded"):
            return json_resp(result, 429)
        return json_resp(result)

    # ── Usage export ─────────────────────────────────────────
    # GET /api/usage/export?org_id=...
    if len(parts) == 4 and parts[3] == "export" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        rows = await svc.export_usage_csv(org_id)
        return json_resp({"rows": rows, "count": len(rows)})

    # ── Alert rule toggle ────────────────────────────────────
    # POST /api/usage/alerts/:rid/toggle
    if (
        len(parts) == 6
        and parts[3] == "alerts"
        and parts[5] == "toggle"
        and method == "POST"
    ):
        try:
            return json_resp(await svc.toggle_alert_rule(parts[4]))
        except ValueError as e:
            return error(str(e), 404)

    # ── Alert rules CRUD ─────────────────────────────────────
    # GET /api/usage/alerts?org_id=...
    if len(parts) == 4 and parts[3] == "alerts" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        return json_resp({"rules": await svc.list_alert_rules(org_id)})

    # POST /api/usage/alerts
    if len(parts) == 4 and parts[3] == "alerts" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_alert_rule(
                org_id=data.get("org_id", ""),
                created_by=uid,
                name=data.get("name", ""),
                alert_type=data.get("alert_type", ""),
                config=data.get("config"),
                threshold_value=data.get("threshold_value", 0),
                comparison=data.get("comparison", "gte"),
                notify_channels=data.get("notify_channels"),
                notify_user_ids=data.get("notify_user_ids"),
                cooldown_minutes=data.get("cooldown_minutes", 60),
                is_active=data.get("is_active", True),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/usage/alerts/:rid
    if len(parts) == 5 and parts[3] == "alerts" and method == "GET":
        try:
            return json_resp(await svc.get_alert_rule(parts[4]))
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/usage/alerts/:rid
    if len(parts) == 5 and parts[3] == "alerts" and method == "PUT":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_alert_rule(parts[4], **data))
        except ValueError as e:
            return error(str(e), 404)

    # DELETE /api/usage/alerts/:rid
    if len(parts) == 5 and parts[3] == "alerts" and method == "DELETE":
        try:
            await svc.delete_alert_rule(parts[4])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
