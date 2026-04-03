from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.common.enums import UserRole
from api.admin.service import AdminService
from api.articles.service import ArticleService
from models.common.enums import ArticleStatus, NotificationType


async def handle_admin(request, env, path, method, query, ctx):
    svc = AdminService(env, ctx)
    article_svc = ArticleService(env, ctx)
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
        page = int(query.get("page", ["1"])[0])
        return json_resp(await svc.get_approval_queue(page))

    # POST /api/admin/queue/bulk — APPROVER+
    if method == "POST" and section == "queue" and target == "bulk":
        if not require_role(user, UserRole.CAN_APPROVE):
            return error("Forbidden", 403)

        payload = await request.json()
        if not isinstance(payload, dict):
            return error("Invalid payload", 422)

        bulk_action = str(payload.get("action", "")).strip().lower()
        if bulk_action not in {"approve", "publish", "reject"}:
            return error("action must be one of: approve, publish, reject", 422)

        article_ids = payload.get("article_ids", [])
        if not isinstance(article_ids, list) or not article_ids:
            return error("article_ids must be a non-empty list", 422)

        if len(article_ids) > 50:
            return error("Max 50 articles per bulk request", 422)

        reject_note = str(payload.get("note") or "").strip()
        if bulk_action == "reject" and not reject_note:
            return error("note is required for reject", 422)

        results = []
        succeeded = 0

        for raw_article_id in article_ids:
            article_id = str(raw_article_id or "").strip()
            if not article_id:
                results.append(
                    {"article_id": "", "ok": False, "error": "Invalid article id"}
                )
                continue

            article = await article_svc.get_by_id_or_slug(article_id)
            if not article:
                results.append(
                    {
                        "article_id": article_id,
                        "ok": False,
                        "error": "Article not found",
                    }
                )
                continue

            try:
                if bulk_action == "approve":
                    if article.status != ArticleStatus.SUBMITTED:
                        raise ValueError("Only SUBMITTED articles can be approved")
                    new_status = await article_svc.transition(
                        article.id,
                        ArticleStatus.APPROVED,
                        actor_id=user["sub"],
                    )
                    if hasattr(article_svc, "notify_user"):
                        await article_svc.notify_user(
                            user_id=article.author_id,
                            type_=NotificationType.APPROVED,
                            message=f"Your article '{article.title}' was approved.",
                            article_id=article.id,
                            actor_id=user["sub"],
                        )
                elif bulk_action == "publish":
                    if article.status != ArticleStatus.APPROVED:
                        raise ValueError("Only APPROVED articles can be published")
                    new_status = await article_svc.transition(
                        article.id, ArticleStatus.PUBLISHED
                    )
                    if hasattr(article_svc, "notify_user"):
                        await article_svc.notify_user(
                            user_id=article.author_id,
                            type_=NotificationType.PUBLISHED,
                            message=f"Your article '{article.title}' is now published.",
                            article_id=article.id,
                            actor_id=user["sub"],
                        )
                else:
                    if article.status != ArticleStatus.SUBMITTED:
                        raise ValueError("Only SUBMITTED articles can be rejected")
                    new_status = await article_svc.transition(
                        article.id,
                        ArticleStatus.REJECTED,
                        note=reject_note,
                    )
                    if hasattr(article_svc, "notify_user"):
                        await article_svc.notify_user(
                            user_id=article.author_id,
                            type_=NotificationType.REJECTED,
                            message=f"Your article '{article.title}' was rejected. {reject_note}",
                            article_id=article.id,
                            actor_id=user["sub"],
                        )

                succeeded += 1
                results.append(
                    {
                        "article_id": article.id,
                        "ok": True,
                        "status": new_status,
                    }
                )
            except ValueError as e:
                results.append(
                    {
                        "article_id": article.id,
                        "ok": False,
                        "error": str(e),
                    }
                )

        return json_resp(
            {
                "action": bulk_action,
                "processed": len(results),
                "succeeded": succeeded,
                "failed": len(results) - succeeded,
                "results": results,
            }
        )

    # GET /api/admin/users — SUPERADMIN
    if method == "GET" and section == "users":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        page = int(query.get("page", ["1"])[0])
        return json_resp(await svc.list_users(page))

    # GET /api/admin/content-types — SUPERADMIN
    if method == "GET" and section == "content-types":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        return json_resp(await svc.list_content_types())

    # GET /api/admin/success-signals — SUPERADMIN
    if method == "GET" and section == "success-signals":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        if target == "history":
            article_id = str(query.get("article_id", [""])[0]).strip()
            hours = int(query.get("hours", ["24"])[0])
            try:
                return json_resp(
                    await svc.list_success_signal_history(
                        article_id=article_id, hours=hours
                    )
                )
            except ValueError as e:
                return error(str(e), 422)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["25"])[0])
        return json_resp(await svc.list_success_signals(page=page, limit=limit))

    # GET /api/admin/ranking — SUPERADMIN
    if method == "GET" and section == "ranking":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        limit = int(query.get("limit", ["10"])[0])
        return json_resp(await svc.get_rankings(limit=limit))

    # GET /api/admin/ranking-weights — SUPERADMIN
    if method == "GET" and section == "ranking-weights":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        return json_resp({"weights": await svc.get_ranking_weights()})

    # POST /api/admin/content-types — SUPERADMIN
    if method == "POST" and section == "content-types":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        try:
            payload = await request.json()
            created = await svc.create_content_type(payload, actor_id=user["sub"])
            return json_resp(created, 201)
        except ValueError as e:
            return error(str(e), 422)

    # PUT /api/admin/ranking-weights — SUPERADMIN
    if method == "PUT" and section == "ranking-weights":
        if not require_role(user, ["SUPERADMIN"]):
            return error("Forbidden", 403)
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                return error("Invalid payload", 422)
            updated = await svc.update_ranking_weights(payload, actor_id=user["sub"])
            return json_resp(updated)
        except ValueError as e:
            return error(str(e), 422)

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
        return json_resp(await svc.get_notifications(user["sub"], page))

    # PUT /api/admin/notifications/read
    if method == "PUT" and section == "notifications" and target == "read":
        await svc.mark_notifications_read(user["sub"])
        return json_resp({"status": "marked read"})

    # PUT /api/admin/notifications/:id/read
    if method == "PUT" and section == "notifications" and target and action == "read":
        try:
            await svc.mark_notification_read(user["sub"], target)
            return json_resp({"status": "marked read"})
        except ValueError as e:
            return error(str(e), 422)

    return error("Not found", 404)
