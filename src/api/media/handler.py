from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.media.service import MediaService


async def handle_media(request, env, path, method, query, ctx):
    svc = MediaService(env, ctx)
    parts = path.rstrip("/").split("/")
    action = parts[3] if len(parts) > 3 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    # POST /api/media/upload
    if method == "POST" and action == "upload":
        try:
            result = await svc.upload(user["sub"], request)
        except ValueError as e:
            return error(str(e), 422)
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
        return json_resp({"deleted": True})

    return error("Not found", 404)
