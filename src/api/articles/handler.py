from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from models.common.enums import Scope, ArticleStatus, UserRole, NotificationType
from models.article.requests import (
    ArticleCreateRequest,
    ArticleUpdateRequest,
    RejectArticleRequest,
)
from api.articles.service import ArticleService
from api.membership.service import MembershipService
from api.feature_flags.service import FeatureFlagService


COLLABORATION_FLAG_KEY = "collaboration_coauthor"


async def handle_articles(request, env, path, method, query, ctx):
    svc = ArticleService(env, ctx)
    parts = path.rstrip("/").split("/")
    art_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None
    single_author_mode = str(getattr(env, "SINGLE_AUTHOR_MODE", "true")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    # GET /api/articles
    if method == "GET" and not art_id:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)  # Max 100 per page
        try:
            result = await svc.list_published(
                page=page,
                limit=limit,
                tag=query.get("tag", [None])[0],
                search=query.get("search", [None])[0],
                content_type=query.get("content_type", [None])[0],
                sort=query.get("sort", [None])[0],
            )
        except TypeError:
            try:
                result = await svc.list_published(
                    page=page,
                    limit=limit,
                    tag=query.get("tag", [None])[0],
                    search=query.get("search", [None])[0],
                    content_type=query.get("content_type", [None])[0],
                )
            except TypeError:
                result = await svc.list_published(
                    page=page,
                    limit=limit,
                    tag=query.get("tag", [None])[0],
                    search=query.get("search", [None])[0],
                )
        return json_resp(result.to_dict())

    # GET /api/articles/mine
    if method == "GET" and art_id == "mine":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        status = query.get("status", [None])[0]
        limit = min(limit, 100)
        result = await svc.list_by_author(user["sub"], page, limit, status)
        return json_resp(result.to_dict())

    # GET /api/articles/content-types
    if method == "GET" and art_id == "content-types":
        content_types = await svc.list_content_types()
        return json_resp({"content_types": content_types})

    # GET /api/articles/:id
    if method == "GET" and art_id and not action:
        article = await svc.get_by_id_or_slug(art_id)
        if not article:
            return error("Article not found", 404)

        # Phase 3: Check paywall enforcement (GAP-015)
        user = await get_user(request, env)
        membership_svc = MembershipService(env, ctx)

        # Only check paywall if membership service is properly initialized
        if membership_svc._db and article.premium_only:
            # Article is premium-only
            if not user:
                # Not logged in; return teaser payload
                return json_resp(
                    {
                        "article": article.to_dict(Scope.DETAIL),
                        "paywall": {
                            "is_premium": True,
                            "has_access": False,
                            "reason": "unauthorized",
                            "teaser_words": article.premium_teaser_words,
                            "upgrade_required": True,
                        },
                    }
                )

            # User is logged in; check if they have access
            has_access = await membership_svc.can_read_premium_article(
                user["sub"], article.id
            )

            if not has_access:
                # User doesn't have access; return paywall
                return json_resp(
                    {
                        "article": article.to_dict(Scope.DETAIL),
                        "paywall": {
                            "is_premium": True,
                            "has_access": False,
                            "reason": "membership_required",
                            "teaser_words": article.premium_teaser_words,
                            "upgrade_required": True,
                        },
                    }
                )
            else:
                # User has access; track the premium read
                await membership_svc.track_premium_read(
                    user_id=user["sub"],
                    article_id=article.id,
                )

        # User has access or article is not premium
        await svc.increment_views(article.id)
        return json_resp({"article": article.to_dict(Scope.DETAIL)})

    # GET /api/articles/:id/schema
    if method == "GET" and art_id and action == "schema":
        article = await svc.get_by_id_or_slug(art_id)
        if not article:
            return error("Article not found", 404)
        return json_resp({"schema": await svc.build_schema(article)})

    # GET /api/articles/:id/series
    if method == "GET" and art_id and action == "series":
        from api.series.service import SeriesService

        series_svc = SeriesService(env, ctx)
        series_info = await series_svc.get_article_series(art_id)
        if not series_info:
            return error("Article not in any series", 404)
        return json_resp({"series": series_info.to_dict()})

    # GET /api/articles/:id/related (Phase 2: Reader Engagement)
    if method == "GET" and art_id and action == "related":
        limit = int(query.get("limit", ["5"])[0])
        limit = min(max(limit, 1), 20)
        related = await svc.get_related(art_id, limit)
        return json_resp(
            {"related": [a.to_dict(Scope.LIST) for a in related], "count": len(related)}
        )

    # POST /api/articles
    if method == "POST" and not art_id:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        if not require_role(user, UserRole.CAN_WRITE):
            return error("Must be AUTHOR or above", 403)
        try:
            req = ArticleCreateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        try:
            article = await svc.create(req, author_id=user["sub"])
        except ValueError as e:
            return error(str(e), 422)
        return json_resp({"article": article.to_dict(Scope.DETAIL)}, 201)

    # PUT /api/articles/:id
    if method == "PUT" and art_id and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        article = await svc.get_by_id_or_slug(art_id)
        if not article:
            return error("Article not found", 404)
        collaboration_enabled = False
        if not single_author_mode:
            flag_svc = FeatureFlagService(env, ctx)
            collaboration_enabled = await flag_svc.evaluate_one(
                COLLABORATION_FLAG_KEY,
                user_id=user["sub"],
                user_role=user.get("role", ""),
                org_id=getattr(article, "org_id", None),
            )
        owner_override_allowed = (
            require_role(user, ["SUPERADMIN"]) and collaboration_enabled
        )
        if article.author_id != user["sub"] and not owner_override_allowed:
            return error("Forbidden", 403)
        if article.status not in ArticleStatus.EDITABLE:
            return error("Can only edit DRAFT or REJECTED articles", 409)
        try:
            req = ArticleUpdateRequest.from_body(await request.json())
        except ValueError as e:
            return error(str(e), 422)
        try:
            updated = await svc.update(art_id, req, article)
        except ValueError as e:
            return error(str(e), 422)
        return json_resp({"article": updated.to_dict(Scope.DETAIL)})

    # DELETE /api/articles/:id
    if method == "DELETE" and art_id and not action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)
        owner = await svc.get_owner(art_id)
        if not owner:
            return error("Article not found", 404)
        collaboration_enabled = False
        if not single_author_mode:
            flag_svc = FeatureFlagService(env, ctx)
            collaboration_enabled = await flag_svc.evaluate_one(
                COLLABORATION_FLAG_KEY,
                user_id=user["sub"],
                user_role=user.get("role", ""),
            )
        owner_override_allowed = (
            require_role(user, ["SUPERADMIN"]) and collaboration_enabled
        )
        if owner != user["sub"] and not owner_override_allowed:
            return error("Forbidden", 403)
        await svc.delete(art_id)
        return json_resp({"deleted": True})

    # Action endpoints
    if method == "POST" and art_id and action:
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        article = await svc.get_by_id_or_slug(art_id)
        if not article:
            return error("Article not found", 404)

        # POST /api/articles/:id/submit
        # POST /api/articles/:id/submit-for-approval
        if action in {"submit", "submit-for-approval"}:
            if article.author_id != user["sub"]:
                return error("Forbidden", 403)
            if article.status not in ArticleStatus.EDITABLE:
                return error("Only DRAFT or REJECTED articles can be submitted", 409)
            moderation = {
                "decision": "pending_admin",
                "state": "AUTO_APPROVED_PENDING_ADMIN",
                "note": "Auto-check passed. Pending admin/superadmin approval.",
            }
            if hasattr(svc, "run_auto_moderation"):
                moderation = await svc.run_auto_moderation(article)
            if moderation["decision"] == "rejected":
                return json_resp(
                    {
                        "status": ArticleStatus.REJECTED,
                        "moderation": moderation,
                    },
                    409,
                )
            new_status = await svc.transition(art_id, ArticleStatus.SUBMITTED)
            return json_resp({"status": new_status, "moderation": moderation})

        # POST /api/articles/:id/duplicate
        if action == "duplicate":
            collaboration_enabled = False
            if not single_author_mode:
                flag_svc = FeatureFlagService(env, ctx)
                collaboration_enabled = await flag_svc.evaluate_one(
                    COLLABORATION_FLAG_KEY,
                    user_id=user["sub"],
                    user_role=user.get("role", ""),
                    org_id=getattr(article, "org_id", None),
                )
            owner_override_allowed = (
                require_role(user, ["SUPERADMIN"]) and collaboration_enabled
            )
            if article.author_id != user["sub"] and not owner_override_allowed:
                return error("Forbidden", 403)

            duplicated = await svc.duplicate_article(art_id, user["sub"])
            if not duplicated:
                return error("Article not found", 404)
            return json_resp({"article": duplicated.to_dict(Scope.DETAIL)}, 201)

        # POST /api/articles/:id/coauthors
        if action == "coauthors":
            if single_author_mode:
                return error("Coauthoring is disabled in single-author mode", 409)

            flag_svc = FeatureFlagService(env, ctx)
            collaboration_enabled = await flag_svc.evaluate_one(
                COLLABORATION_FLAG_KEY,
                user_id=user["sub"],
                user_role=user.get("role", ""),
                org_id=getattr(article, "org_id", None),
            )
            if not collaboration_enabled:
                return error("Coauthor feature is disabled", 403)

            owner_override_allowed = require_role(user, ["SUPERADMIN"])
            if article.author_id != user["sub"] and not owner_override_allowed:
                return error("Forbidden", 403)

            payload = await request.json()
            coauthor_user_id = str(payload.get("user_id", "")).strip()
            if not coauthor_user_id:
                return error("user_id is required", 422)

            try:
                result = await svc.add_coauthor(art_id, coauthor_user_id, user["sub"])
            except ValueError as e:
                message = str(e)
                if message in {"Article not found", "User not found"}:
                    return error(message, 404)
                return error(message, 409)

            status_code = 201 if result.get("added") else 200
            return json_resp(result, status_code)

        # POST /api/articles/:id/approve
        if action == "approve":
            if not require_role(user, UserRole.CAN_APPROVE):
                return error("Forbidden", 403)
            if article.status != ArticleStatus.SUBMITTED:
                return error("Only SUBMITTED articles can be approved", 409)
            new_status = await svc.transition(
                art_id, ArticleStatus.APPROVED, actor_id=user["sub"]
            )
            if hasattr(svc, "notify_user"):
                await svc.notify_user(
                    user_id=article.author_id,
                    type_=NotificationType.APPROVED,
                    message=f"Your article '{article.title}' was approved.",
                    article_id=article.id,
                    actor_id=user["sub"],
                )
            return json_resp({"status": new_status})

        # POST /api/articles/:id/reject
        if action == "reject":
            if not require_role(user, UserRole.CAN_APPROVE):
                return error("Forbidden", 403)
            if article.status != ArticleStatus.SUBMITTED:
                return error("Only SUBMITTED articles can be rejected", 409)
            try:
                req = RejectArticleRequest.from_body(await request.json())
            except ValueError as e:
                return error(str(e), 422)
            new_status = await svc.transition(
                art_id, ArticleStatus.REJECTED, note=req.note
            )
            if hasattr(svc, "notify_user"):
                await svc.notify_user(
                    user_id=article.author_id,
                    type_=NotificationType.REJECTED,
                    message=f"Your article '{article.title}' was rejected. {req.note}",
                    article_id=article.id,
                    actor_id=user["sub"],
                )
            return json_resp({"status": new_status})

        # POST /api/articles/:id/publish
        if action == "publish":
            if not require_role(user, UserRole.CAN_APPROVE):
                return error("Forbidden", 403)
            if article.status != ArticleStatus.APPROVED:
                return error("Only APPROVED articles can be published", 409)
            new_status = await svc.transition(art_id, ArticleStatus.PUBLISHED)
            if hasattr(svc, "notify_user"):
                await svc.notify_user(
                    user_id=article.author_id,
                    type_=NotificationType.PUBLISHED,
                    message=f"Your article '{article.title}' is now published.",
                    article_id=article.id,
                    actor_id=user["sub"],
                )
            return json_resp({"status": new_status})

        # POST /api/articles/:id/archive
        if action == "archive":
            is_owner = article.author_id == user["sub"]
            is_admin = require_role(user, UserRole.CAN_APPROVE)
            if not (is_owner or is_admin):
                return error("Forbidden", 403)
            if article.status == ArticleStatus.ARCHIVED:
                return error("Article already archived", 409)
            new_status = await svc.transition(art_id, ArticleStatus.ARCHIVED)
            return json_resp({"status": new_status})

    # GET /api/articles/author/:user_id
    if method == "GET" and parts[3] == "author" and len(parts) > 4:
        user_id = parts[4]
        page = int(query.get("page", ["1"])[0])
        status = query.get("status", [None])[0]  # Optional: filter by status
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        result = await svc.list_by_author(user_id, page, limit, status)
        return json_resp(result.to_dict())

    return error("Not found", 404)
