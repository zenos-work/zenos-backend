from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.common.enums import Scope, UserRole
from models.user.requests import UpdateProfileRequest, UpdateRoleRequest
from api.users.service import UserService
from api.media.service import MediaService
from api.admin.service import AdminService


async def handle_users(request, env, path, method, query, ctx):
    svc = UserService(env, ctx)
    admin_svc = AdminService(env, ctx)
    parts = path.rstrip("/").split("/")
    user_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None
    target = parts[5] if len(parts) > 5 else None

    # GET /api/users/approvers (AUTHOR+ can see approver roster)
    if method == "GET" and user_id == "approvers":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, UserRole.CAN_WRITE):
            return error("Forbidden", 403)

        users, _total = await svc.list_all(limit=200, offset=0)
        approvers = [
            u for u in users if u.get("role") in UserRole.CAN_APPROVE and u.get("id")
        ]
        return json_resp({"approvers": approvers})

    # POST /api/users/approvers/message (AUTHOR+ sends approval chat message)
    if method == "POST" and user_id == "approvers" and action == "message":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, UserRole.CAN_WRITE):
            return error("Forbidden", 403)

        body = await request.json()
        data = body if isinstance(body, dict) else {}
        message = str(data.get("message", "")).strip()
        article_id = str(data.get("article_id", "")).strip() or None
        mode = str(data.get("mode", "group")).strip().lower()
        selected_ids = data.get("recipient_ids", [])

        if not message:
            return error("Message is required", 422)

        users, _total = await svc.list_all(limit=200, offset=0)
        approver_ids = {
            u.get("id")
            for u in users
            if u.get("role") in UserRole.CAN_APPROVE and u.get("id")
        }

        if mode == "individual":
            if not isinstance(selected_ids, list) or not selected_ids:
                return error("Select at least one approver", 422)
            targets = [uid for uid in selected_ids if uid in approver_ids]
        else:
            targets = list(approver_ids)

        if not targets:
            return error("No approver recipients found", 422)

        for target_id in targets:
            await admin_svc.create_notification(
                user_id=target_id,
                type_="COMMENT",
                message=f"Approval chat: {message}",
                actor_id=user["sub"],
                article_id=article_id,
            )

        return json_resp({"status": "sent", "recipients": len(targets)})

    # GET /api/users  (admin only, paginated list)
    if method == "GET" and not user_id:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN", "APPROVER"]):
            return error("Forbidden", 403)
        page = int(query.get("page", ["1"])[0]) - 1
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)  # Max 100 per page
        users, total = await svc.list_all(limit=limit, offset=page * limit)
        return json_resp(
            {
                "data": users,
                "pagination": {
                    "page": page + 1,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # GET /api/users/me
    if method == "GET" and user_id == "me" and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        result = await svc.get_by_id(user["sub"], scope=Scope.PRIVATE)
        if not result:
            return error("User not found", 404)
        prefs = await svc.get_prefs(user["sub"])
        topics = prefs.get("topics", []) if isinstance(prefs, dict) else []
        user_payload = result.to_dict(Scope.PRIVATE)
        user_payload["needs_topic_preferences"] = len(topics) < 3
        return json_resp({"user": user_payload, "prefs": prefs})

    # GET /api/users/:id
    if method == "GET" and user_id and user_id != "me":
        result = await svc.get_by_id(user_id, scope=Scope.PUBLIC)
        if not result:
            return error("User not found", 404)
        return json_resp({"user": result.to_dict(Scope.PUBLIC)})

    # GET /api/users/me/prefs
    if method == "GET" and user_id == "me" and action == "prefs":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        prefs = await svc.get_prefs(user["sub"])
        return json_resp({"prefs": prefs})

    # GET /api/users/me/reading-history
    if method == "GET" and user_id == "me" and action == "reading-history":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["30"])[0])
        return json_resp(
            await svc.list_reading_history(user["sub"], page=page, limit=limit)
        )

    # PUT /api/users/me/reading-history
    if method == "PUT" and user_id == "me" and action == "reading-history":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        body = await request.json()
        data = body if isinstance(body, dict) else {}

        try:
            item = await svc.upsert_reading_history_item(user["sub"], data)
            return json_resp({"item": item})
        except ValueError as e:
            return error(str(e), 422)

    # DELETE /api/users/me/reading-history/:article_id
    if (
        method == "DELETE"
        and user_id == "me"
        and action == "reading-history"
        and target
    ):
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        try:
            await svc.remove_reading_history_item(user["sub"], target)
            return json_resp({"status": "removed"})
        except ValueError as e:
            return error(str(e), 422)

    # DELETE /api/users/me/reading-history
    if method == "DELETE" and user_id == "me" and action == "reading-history":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        await svc.clear_reading_history(user["sub"])
        return json_resp({"status": "cleared"})

    # PUT /api/users/me
    if method == "PUT" and user_id == "me" and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            req = UpdateProfileRequest.from_body(data)
        except ValueError as e:
            return error(str(e), 422)

        # If request updates only avatar_url, keep existing name untouched.
        avatar_only_update = req.name is None and req.avatar_url is not None
        await svc.update_profile(user["sub"], req, skip_name_update=avatar_only_update)
        return json_resp({"status": "updated"})

    # PUT /api/users/me/prefs
    if method == "PUT" and user_id == "me" and action == "prefs":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        await svc.update_prefs(
            user["sub"],
            topics=data.get("topics", []),
            email_notifs=data.get("email_notifs", 1),
            theme=data.get("theme", "dark"),
            font_family=data.get("font_family", "system"),
            font_size=int(data.get("font_size", 18)),
            content_width=int(data.get("content_width", 720)),
            line_height=float(data.get("line_height", 1.6)),
            code_theme=data.get("code_theme", "github-dark"),
        )
        return json_resp({"status": "updated"})

    # PUT /api/users/me/role  (self upgrade READER → AUTHOR)
    if method == "PUT" and user_id == "me" and action == "role":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        if data.get("role") != UserRole.AUTHOR:
            return error("Self-upgrade to AUTHOR only", 422)
        await svc.self_upgrade_to_author(user["sub"])
        return json_resp({"role": UserRole.AUTHOR})

    # POST /api/users/me/avatar  (upload new avatar)
    if method == "POST" and user_id == "me" and action == "avatar":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        media_svc = MediaService(env, ctx)
        try:
            result = await media_svc.upload(user["sub"], request)
            # Update user profile with new avatar URL
            await svc.update_profile(
                user["sub"],
                UpdateProfileRequest(
                    name=None,  # Keep existing name
                    avatar_url=result["url"],
                ),
                skip_name_update=True,
            )
        except ValueError as e:
            return error(str(e), 422)
        except RuntimeError as e:
            return error(str(e), 503)
        return json_resp(
            {
                "avatar_url": result["url"],
                "key": result["key"],
            },
            201,
        )

    # DELETE /api/users/me/avatar  (remove avatar, revert to default)
    if method == "DELETE" and user_id == "me" and action == "avatar":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        await svc.update_profile(
            user["sub"],
            UpdateProfileRequest(name=None, avatar_url=None),
            skip_name_update=True,
        )
        return json_resp({"avatar_url": None})

    # PUT /api/users/:id/role  (SUPERADMIN sets any role)
    if method == "PUT" and user_id and action == "role":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        try:
            req = UpdateRoleRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        await svc.set_role(user_id, req)
        return json_resp({"role": req.role})

    # PUT /api/users/:id/ban  (SUPERADMIN bans user)
    if method == "PUT" and user_id and action == "ban":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        await svc.ban(user_id)
        return json_resp({"is_active": False})

    # PUT /api/users/:id/unban  (SUPERADMIN unbans user)
    if method == "PUT" and user_id and action == "unban":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        await svc.unban(user_id)
        return json_resp({"is_active": True})

    # DELETE /api/users/me  (user deactivates account)
    if method == "DELETE" and user_id == "me":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        body = await request.json() if request.body else {}
        data = body if isinstance(body, dict) else {}
        # Optional: require password confirmation
        # password = data.get('password')
        # if not verify_password(password, user_id):
        #     return error('Invalid password', 401)
        await svc.ban(user["sub"])
        # TODO: revoke all tokens, delete from KV
        return json_resp({"status": "deactivated"})

    # PUT /api/users/me/accept-terms
    # Called once after user reads and accepts the Writer Content Agreement.
    # Idempotent: second call is a no-op (WHERE terms_accepted_at IS NULL).
    if method == "PUT" and user_id == "me" and action == "accept-terms":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        await (
            env.DB.prepare(
                "UPDATE users"
                " SET terms_accepted_at = datetime('now'),"
                "     updated_at = datetime('now')"
                " WHERE id = ? AND terms_accepted_at IS NULL"
            )
            .bind(user["sub"])
            .run()
        )

        # Re-fetch to return current accepted_at
        row = (
            await env.DB.prepare("SELECT terms_accepted_at FROM users WHERE id = ?")
            .bind(user["sub"])
            .first()
        )

        from models.base import row_get

        return json_resp(
            {
                "terms_accepted": True,
                "terms_accepted_at": row_get(row, "terms_accepted_at"),
            }
        )

    return error("Not found", 404)
