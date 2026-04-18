from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.feature_flags.service import FeatureFlagService


async def handle_feature_flags(request, env, path, method, query, ctx):
    svc = FeatureFlagService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]
    role = user.get("role", "")

    # ── Public endpoints ── evaluate flags for the current user ──

    # GET /api/features — all evaluated flags
    if path.rstrip("/") == "/api/features" and method == "GET":
        org_id = query.get("org_id", [None])[0]
        org_tier = query.get("org_tier", [None])[0]
        membership_tier = query.get("membership_tier", [None])[0]
        result = await svc.evaluate_all(
            user_id=uid,
            user_role=role,
            org_id=org_id,
            org_tier=org_tier,
            membership_tier=membership_tier,
        )
        return json_resp({"flags": result})

    # GET /api/features/:key — evaluate single flag
    if path.startswith("/api/features/") and method == "GET":
        flag_key = parts[3] if len(parts) > 3 else None
        if not flag_key:
            return error("Flag key required", 400)
        org_id = query.get("org_id", [None])[0]
        org_tier = query.get("org_tier", [None])[0]
        membership_tier = query.get("membership_tier", [None])[0]
        enabled = await svc.evaluate_one(
            flag_key,
            user_id=uid,
            user_role=role,
            org_id=org_id,
            org_tier=org_tier,
            membership_tier=membership_tier,
        )
        return json_resp({"flag_key": flag_key, "enabled": enabled})

    # ── Admin endpoints ── CRUD for SUPERADMIN ──

    if not path.startswith("/api/admin/feature-flags"):
        return error("Not found", 404)

    if not require_role(user, ["SUPERADMIN"]):
        return error("Forbidden", 403)

    # GET /api/admin/feature-flags — list all flags
    if method == "GET" and len(parts) <= 4:
        category = query.get("category", [None])[0]
        result = await svc.list_flags(category=category)
        return json_resp(result)

    # GET /api/admin/feature-flags/:id
    if method == "GET" and len(parts) == 5:
        try:
            return json_resp(await svc.get_flag(parts[4]))
        except ValueError as e:
            return error(str(e), 404)

    # POST /api/admin/feature-flags/preview-announcement — preview message and audience
    if method == "POST" and len(parts) == 5 and parts[4] == "preview-announcement":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.preview_announcement(data))
        except ValueError as e:
            return error(str(e), 400)

    # POST /api/admin/feature-flags — create
    if method == "POST" and len(parts) <= 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_flag(
                flag_key=data.get("flag_key", ""),
                name=data.get("name", ""),
                created_by=uid,
                description=data.get("description", ""),
                category=data.get("category", "general"),
                is_active=data.get("is_active", False),
                target_type=data.get("target_type", "global"),
                targets=data.get("targets"),
                rollout_pct=data.get("rollout_pct", 0),
                metadata=data.get("metadata"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # PUT /api/admin/feature-flags/:id/toggle — quick toggle
    if method == "PUT" and len(parts) == 6 and parts[5] == "toggle":
        flag_id = parts[4]
        try:
            result = await svc.toggle_flag(flag_id, updated_by=uid)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/admin/feature-flags/:id — update
    if method == "PUT" and len(parts) == 5:
        flag_id = parts[4]
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.update_flag(
                flag_id=flag_id,
                updated_by=uid,
                name=data.get("name"),
                description=data.get("description"),
                category=data.get("category"),
                is_active=data.get("is_active"),
                target_type=data.get("target_type"),
                targets=data.get("targets"),
                rollout_pct=data.get("rollout_pct"),
                metadata=data.get("metadata"),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/admin/feature-flags/:id — delete
    if method == "DELETE" and len(parts) == 5:
        flag_id = parts[4]
        try:
            await svc.delete_flag(flag_id)
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
