from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.domains.service import DomainService


async def handle_domains(request, env, path, method, query, ctx):
    svc = DomainService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/domains => parts: ['', 'api', 'domains']
    # /api/domains/:id => parts[3]
    # /api/domains/:id/verify => parts[4] = 'verify'
    domain_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # POST /api/domains — register domain
    if method == "POST" and not domain_id:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.register_domain(
                user_id=uid,
                domain=data.get("domain", ""),
                resource_type=data.get("resource_type", "blog"),
                verification_method=data.get("verification_method", "cname"),
                org_id=data.get("org_id"),
                resource_id=data.get("resource_id"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/domains — list domains
    if method == "GET" and not domain_id:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_domains(uid, page=page, limit=limit))

    # POST /api/domains/:id/verify
    if method == "POST" and domain_id and action == "verify":
        try:
            result = await svc.verify_domain(domain_id, uid)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/domains/:id
    if method == "DELETE" and domain_id:
        try:
            await svc.delete_domain(domain_id, uid)
            return json_resp({"status": "deleted"})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
