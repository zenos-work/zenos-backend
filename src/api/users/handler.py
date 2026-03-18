from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.common.enums import Scope, UserRole
from models.user.requests import UpdateProfileRequest, UpdateRoleRequest
from api.users.service import UserService
from api.media.service import MediaService


async def handle_users(request, env, path, method, query, ctx):
    svc = UserService(env, ctx)
    parts = path.rstrip("/").split("/")
    user_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None

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
    if method == "GET" and user_id == "me":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        result = await svc.get_by_id(user["sub"], scope=Scope.PRIVATE)
        if not result:
            return error("User not found", 404)
        return json_resp({"user": result.to_dict(Scope.PRIVATE)})

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

    # PUT /api/users/me
    if method == "PUT" and user_id == "me" and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        try:
            req = UpdateProfileRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        await svc.update_profile(user["sub"], req)
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
