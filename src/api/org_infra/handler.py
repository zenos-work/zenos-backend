from utils.helpers import json_resp, error
from middleware.auth import get_user
from middleware.org_access import require_org_role
from api.org_infra.service import OrgInfraService


async def handle_org_infra(request, env, path, method, query, ctx):
    """Routes for org infrastructure: audit-log, api-keys, sso.

    All routes are under /api/organizations/:id/...
    """
    svc = OrgInfraService(env, ctx)
    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]
    parts = path.rstrip("/").split("/")
    # /api/organizations/:id/audit-log => parts = ['','api','organizations', id, 'audit-log']
    # /api/organizations/:id/api-keys => parts[4] = 'api-keys'
    # /api/organizations/:id/api-keys/:kid => parts[5] = kid
    # /api/organizations/:id/sso => parts[4] = 'sso'

    org_id = parts[3] if len(parts) > 3 else None
    sub = parts[4] if len(parts) > 4 else None

    if not org_id or not sub:
        return error("Not found", 404)

    # ── Audit Log ──────────────────────────────────────────────────────
    if sub == "audit-log" and method == "GET":
        try:
            await require_org_role(env.DB, uid, org_id, "admin")
        except PermissionError as e:
            return error(str(e), 403)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_audit_log(org_id, page=page, limit=limit))

    # ── API Keys ──────────────────────────────────────────────────────
    if sub == "api-keys":
        key_id = parts[5] if len(parts) > 5 else None

        try:
            await require_org_role(env.DB, uid, org_id, "admin")
        except PermissionError as e:
            return error(str(e), 403)

        if method == "POST" and not key_id:
            body = await request.json()
            name = body.get("name")
            if not name:
                return error("name is required", 400)
            result = await svc.create_api_key(
                org_id, name, body.get("scopes", '["read"]'), uid
            )
            return json_resp(result, 201)

        if method == "GET" and not key_id:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_api_keys(org_id, page=page, limit=limit))

        if method == "DELETE" and key_id:
            await svc.revoke_api_key(key_id, org_id)
            return json_resp({"status": "revoked"})

        return error("Not found", 404)

    # ── SSO ────────────────────────────────────────────────────────────
    if sub == "sso":
        try:
            await require_org_role(env.DB, uid, org_id, "owner")
        except PermissionError as e:
            return error(str(e), 403)

        if method == "POST":
            body = await request.json()
            try:
                result = await svc.create_sso(
                    org_id,
                    body.get("provider"),
                    body.get("metadata", "{}"),
                    body.get("is_enabled", 0),
                    uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        if method == "PUT":
            body = await request.json()
            try:
                return json_resp(
                    await svc.update_sso(
                        org_id,
                        body.get("provider"),
                        body.get("metadata", "{}"),
                        body.get("is_enabled", 0),
                    )
                )
            except ValueError as e:
                return error(str(e), 400)

        if method == "GET":
            try:
                return json_resp(await svc.get_sso(org_id))
            except ValueError as e:
                return error(str(e), 404)

        return error("Not found", 404)

    return error("Not found", 404)
