from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.tag.requests import TagCreateRequest
from api.tags.service import TagService


async def handle_tags(request, env, path, method, query, ctx):
    svc = TagService(env, ctx)
    parts = path.rstrip("/").split("/")
    tag_id = parts[3] if len(parts) > 3 else None

    # GET /api/tags
    if method == "GET" and not tag_id:
        tags = await svc.list_all()
        return json_resp({"tags": [t.to_dict() for t in tags]})

    # GET /api/tags/:slug_or_id
    if method == "GET" and tag_id:
        tag = await svc.get_by_slug_or_id(tag_id)
        if not tag:
            return error("Tag not found", 404)
        return json_resp({"tag": tag.to_dict()})

    # POST /api/tags — SUPERADMIN only
    if method == "POST":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        try:
            req = TagCreateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        tag = await svc.create(req)
        return json_resp({"tag": tag.to_dict()}, 201)

    return error("Not found", 404)
