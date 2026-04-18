from js import Response, Headers

from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.media.service import MediaService


def _extract_content_type(obj):
    metadata = getattr(obj, "httpMetadata", None)
    if not metadata:
        return None

    getter = getattr(metadata, "get", None)
    if callable(getter):
        try:
            content_type = getter("contentType")
            if content_type:
                return str(content_type)
        except Exception:
            pass

    content_type = getattr(metadata, "contentType", None)
    if content_type:
        return str(content_type)

    to_py = getattr(metadata, "to_py", None)
    if callable(to_py):
        try:
            metadata = to_py()
        except TypeError:
            metadata = to_py(depth=3)

    if isinstance(metadata, dict):
        content_type = metadata.get("contentType")
        if content_type:
            return str(content_type)

    return None


async def handle_media(request, env, path, method, query, ctx):
    svc = MediaService(env, ctx)
    parts = path.rstrip("/").split("/")
    action = parts[3] if len(parts) > 3 else None

    # Public media access: GET /api/media/:key
    if method == "GET" and action and action != "upload":
        key = "/".join(parts[3:])
        range_header = request.headers.get("Range")
        r2_options = None
        if range_header and range_header.startswith("bytes="):
            try:
                r_val = range_header.split("=")[1].split("-")
                start = int(r_val[0])
                r2_options = {"range": {"offset": start}}
                if r_val[1]:
                    end = int(r_val[1])
                    r2_options["range"]["length"] = end - start + 1
            except (ValueError, IndexError):
                pass

        try:
            obj = await svc.get_public(key, r2_options)
        except RuntimeError as e:
            return error(str(e), 503)
        if not obj:
            return error("Media not found", 404)

        content_type = _extract_content_type(obj)
        if not content_type:
            content_type = "application/octet-stream"

        headers = Headers.new(
            [
                ("Content-Type", content_type),
                ("Cache-Control", "public, max-age=31536000, immutable"),
                ("Access-Control-Allow-Origin", "*"),
                ("Accept-Ranges", "bytes"),
            ]
        )

        status = 200
        if hasattr(obj, "range") and obj.range:
            status = 206
            total = getattr(obj, "totalSize", obj.size)
            headers.set(
                "Content-Range",
                f"bytes {obj.range.offset}-{obj.range.offset + obj.size - 1}/{total}",
            )

        return Response.new(obj.body, status=status, headers=headers)

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
