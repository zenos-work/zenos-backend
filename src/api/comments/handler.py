from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.comment.requests import (
    CommentCreateRequest,
    CommentUpdateRequest,
    CommentModerateRequest,
)
from api.comments.service import CommentService


async def handle_comments(request, env, path, method, query, ctx):
    svc = CommentService(env, ctx)
    parts = path.rstrip("/").split("/")
    comment_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None
    article_id = query.get("article_id", [None])[0]

    # ── Admin: GET /api/comments/admin/all (list all comments for moderation) ──
    if method == "GET" and parts[-2:] == ["admin", "all"]:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN", "APPROVER"]):
            return error("Forbidden", 403)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        comments, total = await svc.list_all_for_moderation(page, limit)
        return json_resp(
            {
                "data": [c.to_dict() for c in comments],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # GET /api/comments?article_id=xxx (with nested replies)
    if method == "GET" and not comment_id and not action:
        if not article_id:
            return error("article_id query param required", 422)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        comments, total = await svc.list_for_article_with_replies(
            article_id, page, limit
        )
        return json_resp(
            {
                "data": [c.to_dict() for c in comments],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # POST /api/comments (create comment or reply)
    if method == "POST" and not comment_id:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        try:
            req = CommentCreateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        try:
            cid = await svc.create(req, author_id=user["sub"])
            comment = await svc.get_by_id(cid)
            return json_resp({"comment": comment.to_dict()}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/comments/:id/replies (lazy-load nested replies)
    if method == "GET" and comment_id and action == "replies":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        try:
            replies, total = await svc.list_replies(comment_id, page, limit)
            return json_resp(
                {
                    "data": [r.to_dict() for r in replies],
                    "pagination": {
                        "page": page,
                        "limit": limit,
                        "total": total,
                        "pages": (total + limit - 1) // limit,
                    },
                }
            )
        except ValueError:
            return error("Parent comment not found", 404)

    # PUT /api/comments/:id (edit own comment)
    if method == "PUT" and comment_id and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        try:
            req = CommentUpdateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        try:
            await svc.update(comment_id, req, requesting_user_id=user["sub"])
            comment = await svc.get_by_id(comment_id)
            return json_resp({"comment": comment.to_dict()})
        except ValueError as e:
            return error(str(e), 404)
        except PermissionError:
            return error("Forbidden", 403)

    # DELETE /api/comments/:id (soft delete by author or admin)
    if method == "DELETE" and comment_id and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        try:
            await svc.delete(
                comment_id,
                requesting_user_id=user["sub"],
                is_superadmin=require_role(user, ["SUPERADMIN"]),
            )
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)
        except PermissionError:
            return error("Forbidden", 403)

    # POST /api/comments/:id/flag (flag as spam — authenticated users)
    if method == "POST" and comment_id and action == "flag":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        try:
            await svc.flag_spam(comment_id, user["sub"])
            return json_resp({"flagged": True})
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/comments/:id/moderate (admin: hide/unhide for moderation)
    if method == "PUT" and comment_id and action == "moderate":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN", "APPROVER"]):
            return error("Forbidden", 403)
        try:
            req = CommentModerateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        try:
            await svc.moderate(comment_id, req, moderator_id=user["sub"])
            return json_resp({"moderated": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
