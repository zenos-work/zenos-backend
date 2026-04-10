"""Phase 9 Step 32 — Community handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.community.service import CommunityService


async def handle_community(request, env, path, method, query, ctx):
    svc = CommunityService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Members sub-resource ─────────────────────────────────
    # /api/community/:sid/members[/:user_id]
    if len(parts) >= 5 and parts[4] == "members":
        space_id = parts[3]
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_members(space_id, page, limit))
        if method == "POST" and len(parts) == 5:
            try:
                return json_resp(await svc.join_space(space_id, uid), 201)
            except ValueError as e:
                return error(str(e), 409)
        if method == "DELETE" and len(parts) == 5:
            try:
                return json_resp(await svc.leave_space(space_id, uid))
            except ValueError as e:
                return error(str(e), 400)
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_member_role(
                        space_id, parts[5], data.get("role", "member")
                    )
                )
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Posts sub-resource ───────────────────────────────────
    # /api/community/:sid/posts[/:pid][/replies|/like]
    if len(parts) >= 5 and parts[4] == "posts":
        space_id = parts[3]
        # Replies sub-sub-resource
        if len(parts) >= 7 and parts[6] == "replies":
            post_id = parts[5]
            if method == "GET":
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["20"])[0])
                return json_resp(await svc.list_replies(post_id, page, limit))
            return error("Not found", 404)
        # Like action
        if len(parts) >= 7 and parts[6] == "like":
            if method == "POST":
                try:
                    return json_resp(await svc.like_post(parts[5]))
                except ValueError as e:
                    return error(str(e), 404)
            return error("Not found", 404)
        # GET /api/community/:sid/posts
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_posts(space_id, page, limit))
        # POST /api/community/:sid/posts
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_post(
                    space_id=space_id,
                    author_id=uid,
                    title=data.get("title", ""),
                    body=data.get("body", ""),
                    post_type=data.get("post_type", "discussion"),
                    article_id=data.get("article_id", ""),
                    parent_id=data.get("parent_id", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/community/:sid/posts/:pid
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_post(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/community/:sid/posts/:pid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_post(parts[5], **data))
            except ValueError as e:
                return error(str(e), 404)
        # DELETE /api/community/:sid/posts/:pid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_post(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Spaces CRUD ──────────────────────────────────────────
    # GET /api/community
    if method == "GET" and len(parts) == 3:
        org_id = query.get("org_id", [""])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        if org_id:
            return json_resp(await svc.list_spaces(org_id, page, limit))
        return json_resp(await svc.list_spaces_public(page, limit))
    # POST /api/community
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_space(
                org_id=data.get("org_id", ""),
                created_by=uid,
                name=data.get("name", ""),
                slug=data.get("slug", ""),
                description=data.get("description", ""),
                cover_image_url=data.get("cover_image_url", ""),
                icon=data.get("icon", ""),
                space_type=data.get("space_type", "open"),
                membership_tier=data.get("membership_tier", ""),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
    # GET /api/community/:sid
    if method == "GET" and len(parts) == 4:
        try:
            return json_resp(await svc.get_space(parts[3]))
        except ValueError as e:
            return error(str(e), 404)
    # PUT /api/community/:sid
    if method == "PUT" and len(parts) == 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_space(parts[3], **data))
        except ValueError as e:
            return error(str(e), 404)
    # DELETE /api/community/:sid
    if method == "DELETE" and len(parts) == 4:
        try:
            await svc.delete_space(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
