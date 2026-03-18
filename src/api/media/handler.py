from js import Response, Headers

from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.media.service import MediaService


async def handle_media(request, env, path, method, query, ctx):
    svc = MediaService(env, ctx)
    parts = path.rstrip("/").split("/")
    action = parts[3] if len(parts) > 3 else None

    # Public media access: GET /api/media/:key
    if method == "GET" and action and action != "upload":
        key = "/".join(parts[3:])
        try:
            obj = await svc.get_public(key)
        except RuntimeError as e:
            return error(str(e), 503)
        if not obj:
            return error("Media not found", 404)

        content_type = None
        if getattr(obj, "httpMetadata", None):
            content_type = obj.httpMetadata.get("contentType")
        if not content_type:
            content_type = "application/octet-stream"

        headers = Headers.new(
            [
                ("Content-Type", content_type),
                ("Cache-Control", "public, max-age=31536000, immutable"),
                ("Access-Control-Allow-Origin", "*"),
            ]
        )
        return Response.new(obj.body, status=200, headers=headers)

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    # POST /api/media/upload
    if method == "POST" and action == "upload":
        try:
            result = await svc.upload(user["sub"], request)
        except ValueError as e:
            return error(str(e), 422)
        except RuntimeError as e:
            return error(str(e), 503)
        return json_resp(result, 201)

    # DELETE /api/media/:key
    if method == "DELETE" and action:
        key = "/".join(parts[3:])
        try:
            await svc.delete(
                user["sub"],
                key,
                is_superadmin=require_role(user, ["SUPERADMIN"]),
            )
        except PermissionError:
            return error("Forbidden", 403)
        except RuntimeError as e:
            return error(str(e), 503)
        return json_resp({"deleted": True})

    return error("Not found", 404)
