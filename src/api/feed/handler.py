import json
from utils.helpers import json_resp, error
from middleware.auth import get_user
from models.common.enums import Scope
from api.feed.service import FeedService


async def handle_feed(request, env, path, method, query, ctx):
    svc = FeedService(env, ctx)
    parts = path.rstrip("/").split("/")
    feed_type = parts[3] if len(parts) > 3 else "home"

    if method != "GET":
        return error("Method not allowed", 405)

    page = int(query.get("page", ["1"])[0])
    user = await get_user(request, env)

    if feed_type == "home":
        topics = []
        if user:
            # Load user topic preferences if logged in
            prefs_row = (
                await env.DB.prepare(
                    "SELECT topics FROM user_preferences WHERE user_id = ?"
                )
                .bind(user["sub"])
                .first()
            )
            if prefs_row:
                from models.base import row_get

                raw = row_get(prefs_row, "topics", "[]")
                try:
                    topics = json.loads(raw) if isinstance(raw, str) else raw
                except Exception:
                    topics = []
        result = await svc.home(
            page, user_id=user["sub"] if user else None, topics=topics
        )
        return json_resp(
            {
                "articles": [a.to_dict(Scope.LIST) for a in result["articles"]],
                "feed": result["feed"],
                "page": result["page"],
                "has_more": result["has_more"],
            }
        )

    if feed_type == "featured":
        articles = await svc.featured()
        return json_resp({"articles": [a.to_dict(Scope.LIST) for a in articles]})

    if feed_type == "following":
        if not user:
            return error("Unauthorised", 401)
        result = await svc.following(user["sub"], page)
        return json_resp(
            {
                "articles": [a.to_dict(Scope.LIST) for a in result["articles"]],
                "feed": result["feed"],
                "page": result["page"],
                "has_more": result["has_more"],
            }
        )

    if feed_type == "trending":
        result = await svc.trending(page)
        return json_resp(
            {
                "articles": [a.to_dict(Scope.LIST) for a in result["articles"]],
                "feed": result["feed"],
                "page": result["page"],
                "has_more": result["has_more"],
            }
        )

    return error("Not found", 404)
