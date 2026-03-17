from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.common.enums import UserRole
from api.admin.service import AdminService


async def handle_admin(request, env, path, method, query, ctx):
    svc = AdminService(env, ctx)
    parts = path.rstrip("/").split("/")
    section = parts[3] if len(parts) > 3 else None
    target = parts[4] if len(parts) > 4 else None
    action = parts[5] if len(parts) > 5 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    # GET /api/admin/stats — SUPERADMIN
    if method == "GET" and section == "stats":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        return json_resp(await svc.get_stats())

    # GET /api/admin/queue — APPROVER+
    if method == "GET" and section == "queue":
        if not require_role(user, UserRole.CAN_APPROVE):
            return error("Forbidden", 403)
        return json_resp({"queue": await svc.get_approval_queue()})

    # GET /api/admin/users — SUPERADMIN
    if method == "GET" and section == "users":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        page = int(query.get("page", ["1"])[0])
        return json_resp({"users": await svc.list_users(page)})

    # PUT /api/admin/users/:id/ban
    if method == "PUT" and section == "users" and target and action == "ban":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        await svc.ban_user(target)
        return json_resp({"status": "banned"})

    # PUT /api/admin/users/:id/unban
    if method == "PUT" and section == "users" and target and action == "unban":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        await svc.unban_user(target)
        return json_resp({"status": "unbanned"})

    # GET /api/admin/notifications — own notifications
    if method == "GET" and section == "notifications":
        page = int(query.get("page", ["1"])[0])
        notifications = await svc.get_notifications(user["sub"], page)
        return json_resp({"notifications": notifications})

    # PUT /api/admin/notifications/read
    if method == "PUT" and section == "notifications" and target == "read":
        await svc.mark_notifications_read(user["sub"])
        return json_resp({"status": "marked read"})

    return error("Not found", 404)
