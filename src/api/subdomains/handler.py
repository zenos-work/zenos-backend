"""Phase 11 Step 41 — Subdomain provisioning handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.subdomains.service import SubdomainService


async def handle_subdomains(request, env, path, method, query, ctx):
    svc = SubdomainService(env, ctx)
    parts = path.rstrip("/").split("/")

    # ── Public: /.well-known/org-info ────────────────────────
    if path.startswith("/.well-known/org-info"):
        host = request.headers.get("Host", "")
        subdomain = host.split(".")[0] if "." in host else ""
        if not subdomain:
            subdomain = query.get("subdomain", [""])[0] if query else ""
        if not subdomain:
            return error("Missing subdomain", 400)
        info = await svc.org_info(subdomain)
        if not info:
            return error("Organization not found", 404)
        return json_resp(info)

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── SUPERADMIN: POST /api/admin/organizations/:id/subdomain ──
    if path.startswith("/api/admin/organizations/") and path.endswith("/subdomain"):
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        org_id = parts[4] if len(parts) >= 5 else ""
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.provision(
                    org_id=org_id,
                    subdomain=data.get("subdomain", ""),
                    provisioned_by=uid,
                    custom_domain=data.get("custom_domain", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        if method == "DELETE":
            return json_resp(await svc.delete(org_id))
        return error("Not found", 404)

    # ── SUPERADMIN: GET /api/admin/subdomains ─────────────────
    if path.startswith("/api/admin/subdomains"):
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        if method == "GET":
            limit = int(query.get("limit", [50])[0]) if query else 50
            offset = int(query.get("offset", [0])[0]) if query else 0
            items = await svc.list_all(limit, offset)
            return json_resp({"subdomains": items})
        return error("Not found", 404)

    # ── Org owner: PUT /api/organizations/:id/subdomain ──────
    if path.startswith("/api/organizations/") and path.endswith("/subdomain"):
        org_id = parts[3] if len(parts) >= 4 else ""
        if method == "PUT":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update(org_id, data.get("subdomain", ""))
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        if method == "GET":
            cfg = await svc.get_by_org(org_id)
            if not cfg:
                return error("No subdomain configured", 404)
            return json_resp(cfg)
        if method == "DELETE":
            return json_resp(await svc.deactivate(org_id))
        return error("Not found", 404)

    return error("Not found", 404)
