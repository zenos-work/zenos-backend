from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.add_ons.service import AddOnService


async def handle_add_ons(request, env, path, method, query, ctx):
    """Routes for add-on management.

    Admin routes (SUPERADMIN):
        POST   /api/admin/organizations/:id/add-ons
        PUT    /api/admin/organizations/:id/add-ons/:type
        DELETE /api/admin/organizations/:id/add-ons/:type
        GET    /api/admin/organizations/:id/add-ons
        GET    /api/admin/add-ons/summary

    Org routes:
        GET    /api/organizations/:id/add-ons
        GET    /api/organizations/:id/add-ons/:type/usage
    """
    svc = AddOnService(env, ctx)
    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]
    parts = path.rstrip("/").split("/")

    # ── Admin routes (/api/admin/...) ──────────────────────────────────
    if path.startswith("/api/admin/add-ons/summary"):
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        return json_resp(await svc.summary())

    if path.startswith("/api/admin/organizations/"):
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        # /api/admin/organizations/:id/add-ons => parts: ['','api','admin','organizations', id, 'add-ons']
        org_id = parts[4] if len(parts) > 4 else None
        addon_type = parts[6] if len(parts) > 6 else None

        if method == "POST" and not addon_type:
            body = await request.json()
            try:
                result = await svc.enable_add_on(
                    org_id,
                    body.get("add_on_type"),
                    body.get("tier", "basic"),
                    uid,
                    body.get("limits", "{}"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        if method == "GET" and not addon_type:
            return json_resp(await svc.list_add_ons(org_id))

        if method == "PUT" and addon_type:
            body = await request.json()
            try:
                return json_resp(
                    await svc.update_add_on(
                        org_id, addon_type, body.get("tier"), body.get("limits", "{}")
                    )
                )
            except ValueError as e:
                return error(str(e), 400)

        if method == "DELETE" and addon_type:
            try:
                await svc.disable_add_on(org_id, addon_type)
                return json_resp({"status": "disabled"})
            except ValueError as e:
                return error(str(e), 400)

        return error("Not found", 404)

    # ── Org routes (/api/organizations/:id/add-ons) ────────────────────
    if path.startswith("/api/organizations/"):
        # /api/organizations/:id/add-ons => parts: ['','api','organizations', id, 'add-ons']
        org_id = parts[3] if len(parts) > 3 else None
        addon_type = parts[5] if len(parts) > 5 else None
        usage = parts[6] if len(parts) > 6 else None

        if method == "GET" and not addon_type:
            return json_resp(await svc.list_add_ons(org_id))

        if method == "GET" and addon_type and usage == "usage":
            try:
                return json_resp(await svc.get_usage(org_id, addon_type))
            except ValueError as e:
                return error(str(e), 404)

    return error("Not found", 404)
