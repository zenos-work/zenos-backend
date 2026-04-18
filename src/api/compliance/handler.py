"""Phase 12 Step 48 — GDPR compliance handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.compliance.export_service import ExportService
from api.compliance.erasure_service import ErasureService
from api.feature_flags.service import FeatureFlagService


async def _is_feature_enabled(env, ctx, user, flag_key: str) -> bool:
    if getattr(env, "DB", None) is None:
        return True
    try:
        svc = FeatureFlagService(env, ctx)
        return await svc.evaluate_one(
            flag_key,
            user_id=user.get("sub"),
            user_role=user.get("role", ""),
        )
    except Exception:
        return False


async def handle_compliance(request, env, path, method, query, ctx):
    export_svc = ExportService(env.DB, ctx)
    erasure_svc = ErasureService(env.DB, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    uid = user.get("sub", "")

    # POST /api/users/me/data-export
    if path.rstrip("/") == "/api/users/me/data-export" and method == "POST":
        rid = await export_svc.request_export(uid)
        return json_resp({"id": rid, "status": "pending"}, 201)

    # GET /api/users/me/data-export/:id
    if path.startswith("/api/users/me/data-export/") and method == "GET":
        rid = parts[5] if len(parts) > 5 else ""
        item = await export_svc.get_export(uid, rid)
        if not item:
            return error("Export request not found", 404)
        return json_resp(item)

    # POST /api/users/me/erase
    if path.rstrip("/") == "/api/users/me/erase" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        confirmed = bool(data.get("password_confirmed", False))
        try:
            rid = await erasure_svc.request_erasure(uid, confirmed)
            return json_resp(
                {"id": rid, "status": "pending", "cooling_off_days": 30}, 201
            )
        except ValueError as e:
            return error(str(e), 400)

    # Admin-only compliance routes
    if path.startswith("/api/admin/compliance"):
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        if not await _is_feature_enabled(env, ctx, user, "admin_compliance"):
            return error("Feature 'admin_compliance' is disabled", 403)

        # GET /api/admin/compliance/erasure-queue
        if (
            path.rstrip("/") == "/api/admin/compliance/erasure-queue"
            and method == "GET"
        ):
            items = await erasure_svc.queue()
            return json_resp({"items": items})

        # POST /api/admin/compliance/erasure/:id/execute
        if (
            path.startswith("/api/admin/compliance/erasure/")
            and path.endswith("/execute")
            and method == "POST"
        ):
            rid = parts[5] if len(parts) > 5 else ""
            try:
                result = await erasure_svc.execute_erasure(rid, uid)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 404)

    return error("Not found", 404)
