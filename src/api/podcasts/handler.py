"""Phase 9 Step 35 — Podcast handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.podcasts.service import PodcastService
from api.feature_flags.service import FeatureFlagService


async def _is_feature_enabled(env, ctx, user, flag_key: str) -> bool:
    if getattr(env, "DB", None) is None:
        return True
    try:
        svc = FeatureFlagService(env, ctx)
        return await svc.evaluate_one(
            flag_key,
            user_id=user.get("sub"),
            user_role=user.get("role", ""),
        )
    except Exception:
        return False


async def handle_podcasts(request, env, path, method, query, ctx):
    svc = PodcastService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    if not await _is_feature_enabled(env, ctx, user, "podcasts"):
        return error("Feature 'podcasts' is disabled", 403)

    # ── Episodes sub-resource ────────────────────────────────
    # /api/podcasts/:sid/episodes[/:eid]
    if len(parts) >= 5 and parts[4] == "episodes":
        show_id = parts[3]
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_episodes(show_id, page, limit))
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_episode(
                    show_id=show_id,
                    title=data.get("title", ""),
                    audio_url=data.get("audio_url", ""),
                    description=data.get("description", ""),
                    duration_seconds=data.get("duration_seconds", 0),
                    episode_number=data.get("episode_number", 0),
                    transcript_article_id=data.get("transcript_article_id", ""),
                    published_at=data.get("published_at", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_episode(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_episode(parts[5], **data))
            except ValueError as e:
                return error(str(e), 404)
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_episode(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Shows CRUD ───────────────────────────────────────────
    if method == "GET" and len(parts) == 3:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        owner_id = query.get("owner_id", [None])[0]
        if owner_id:
            shows = await svc.list_shows_by_owner(owner_id)
            return json_resp({"shows": shows})
        return json_resp(await svc.list_shows(page, limit))
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_show(
                owner_id=uid,
                title=data.get("title", ""),
                slug=data.get("slug", ""),
                org_id=data.get("org_id", ""),
                description=data.get("description", ""),
                cover_image_url=data.get("cover_image_url", ""),
                rss_feed_url=data.get("rss_feed_url", ""),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
    if method == "GET" and len(parts) == 4:
        try:
            return json_resp(await svc.get_show(parts[3]))
        except ValueError as e:
            return error(str(e), 404)
    if method == "PUT" and len(parts) == 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_show(parts[3], **data))
        except ValueError as e:
            return error(str(e), 404)
    if method == "DELETE" and len(parts) == 4:
        try:
            await svc.delete_show(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
