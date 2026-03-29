from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.social.service import SocialService


async def handle_social(request, env, path, method, query, ctx):
    svc = SocialService(env, ctx)
    parts = path.rstrip("/").split("/")
    action = (
        parts[3] if len(parts) > 3 else None
    )  # likes | bookmarks | follows | followers | following
    target = parts[4] if len(parts) > 4 else None  # article_id or user_id
    subaction = parts[5] if len(parts) > 5 else None  # check, stats, etc.

    user = await get_user(request, env)
    uid = user["sub"] if user else None

    # Allow public fetch of reaction stats; all other endpoints require auth.
    if not uid and not (action == "reactions" and target and method == "GET"):
        return error("Unauthorised", 401)

    # ── LIKES ──────────────────────────────────────
    # POST /api/social/likes/:article_id — Like an article
    if action == "likes" and target and method == "POST":
        try:
            result = await svc.toggle_like(uid, target, add=True)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # DELETE /api/social/likes/:article_id — Unlike an article
    if action == "likes" and target and method == "DELETE":
        try:
            result = await svc.toggle_like(uid, target, add=False)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # GET /api/social/likes/:article_id/check — Check if user liked
    if action == "likes" and target and subaction == "check" and method == "GET":
        try:
            has_liked = await svc.check_liked(uid, target)
            return json_resp({"has_liked": has_liked})
        except ValueError as e:
            return error(str(e), 404)

    # GET /api/social/likes/:article_id/stats — Get like stats
    if action == "likes" and target and subaction == "stats" and method == "GET":
        try:
            stats = await svc.get_like_stats(target)
            return json_resp(stats)
        except ValueError as e:
            return error(str(e), 404)

    # ── DISLIKES ───────────────────────────────────
    # POST /api/social/dislikes/:article_id — Dislike an article
    if action == "dislikes" and target and method == "POST":
        try:
            result = await svc.toggle_dislike(uid, target, add=True)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # DELETE /api/social/dislikes/:article_id — Remove dislike
    if action == "dislikes" and target and method == "DELETE":
        try:
            result = await svc.toggle_dislike(uid, target, add=False)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # GET /api/social/dislikes/:article_id/check — Check if user disliked
    if action == "dislikes" and target and subaction == "check" and method == "GET":
        try:
            has_disliked = await svc.check_disliked(uid, target)
            return json_resp({"has_disliked": has_disliked})
        except ValueError as e:
            return error(str(e), 404)

    # GET /api/social/dislikes/:article_id/stats — Get dislike stats
    if action == "dislikes" and target and subaction == "stats" and method == "GET":
        try:
            stats = await svc.get_dislike_stats(target)
            return json_resp(stats)
        except ValueError as e:
            return error(str(e), 404)

    # ── SHARES ─────────────────────────────────────
    # POST /api/social/shares/:article_id — Record a share event (LinkedIn-only for now)
    if action == "shares" and target and method == "POST":
        try:
            body = await request.json()
            provider = (
                body.get("provider", "linkedin")
                if isinstance(body, dict)
                else "linkedin"
            )
            result = await svc.share_article(uid, target, provider)
            return json_resp({"share": result})
        except ValueError as e:
            status = 400 if "Unsupported provider" in str(e) else 409
            return error(str(e), status)

    # GET /api/social/shares/:article_id/stats — Get share stats
    if action == "shares" and target and subaction == "stats" and method == "GET":
        try:
            stats = await svc.get_share_stats(target)
            return json_resp(stats)
        except ValueError as e:
            return error(str(e), 404)

    # ── REACTIONS ─────────────────────────────────
    # GET /api/social/reactions/:article_id — Get reaction counts (+ user flags if authenticated)
    if action == "reactions" and target and method == "GET":
        try:
            stats = await svc.get_reactions(target, uid)
            return json_resp(stats)
        except ValueError as e:
            return error(str(e), 400)

    # POST /api/social/reactions/:article_id — Toggle one reaction
    if action == "reactions" and target and method == "POST":
        if not uid:
            return error("Unauthorised", 401)
        try:
            body = await request.json()
            reaction_type = (
                body.get("reaction_type") if isinstance(body, dict) else None
            )
            if not reaction_type:
                return error("reaction_type is required", 422)
            result = await svc.toggle_reaction(uid, target, reaction_type)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 422)

    # DELETE /api/social/reactions/:article_id/:reaction_type — Remove reaction explicitly
    if action == "reactions" and target and subaction and method == "DELETE":
        if not uid:
            return error("Unauthorised", 401)
        try:
            result = await svc.remove_reaction(uid, target, subaction)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 422)

    # ── BOOKMARKS ──────────────────────────────────
    # GET /api/social/bookmarks — List user's bookmarked articles
    if action == "bookmarks" and not target and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        articles, total = await svc.get_bookmarks(uid, page, limit)
        return json_resp(
            {
                "data": [a.to_dict() for a in articles],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # POST /api/social/bookmarks/:article_id — Bookmark an article
    if action == "bookmarks" and target and method == "POST":
        try:
            result = await svc.toggle_bookmark(uid, target, add=True)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # DELETE /api/social/bookmarks/:article_id — Unbookmark an article
    if action == "bookmarks" and target and method == "DELETE":
        try:
            result = await svc.toggle_bookmark(uid, target, add=False)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # GET /api/social/bookmarks/:article_id/check — Check if bookmarked
    if action == "bookmarks" and target and subaction == "check" and method == "GET":
        try:
            has_bookmarked = await svc.check_bookmarked(uid, target)
            return json_resp({"has_bookmarked": has_bookmarked})
        except ValueError as e:
            return error(str(e), 404)

    # ── FOLLOWS ────────────────────────────────────
    # POST /api/social/follows/:user_id — Follow a user
    if action == "follows" and target and method == "POST":
        try:
            result = await svc.toggle_follow(uid, target, add=True)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # DELETE /api/social/follows/:user_id — Unfollow a user
    if action == "follows" and target and method == "DELETE":
        try:
            result = await svc.toggle_follow(uid, target, add=False)
            return json_resp({"action": result.to_dict()})
        except ValueError as e:
            return error(str(e), 409)

    # GET /api/social/follows/:user_id/check — Check if following
    if action == "follows" and target and subaction == "check" and method == "GET":
        try:
            is_following = await svc.check_following(uid, target)
            return json_resp({"is_following": is_following})
        except ValueError as e:
            return error(str(e), 404)

    # ── FOLLOWERS ──────────────────────────────────
    # GET /api/social/followers/:user_id — List user's followers
    if action == "followers" and target and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        followers, total = await svc.list_followers(target, page, limit)
        return json_resp(
            {
                "data": [u.to_dict() for u in followers],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # ── FOLLOWING ──────────────────────────────────
    # GET /api/social/following/:user_id — List users that :user_id follows
    if action == "following" and target and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        limit = min(limit, 100)
        following, total = await svc.list_following(target, page, limit)
        return json_resp(
            {
                "data": [u.to_dict() for u in following],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit,
                },
            }
        )

    # ── USER STATS ────────────────────────────────
    # GET /api/social/stats/:user_id — Get user's social stats
    if action == "stats" and target and method == "GET":
        try:
            stats = await svc.get_user_social_stats(target)
            return json_resp(stats)
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
