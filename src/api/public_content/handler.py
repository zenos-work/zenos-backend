"""Public Content API (SR-023): read-only article and tag surfaces for external consumers."""

from utils.helpers import json_resp, error
from api.articles.service import ArticleService
from api.tags.service import TagService
from models.common.enums import Scope, ArticleStatus


async def handle_public_content(request, env, path, method, query, ctx):
    article_svc = ArticleService(env, ctx)
    tag_svc = TagService(env, ctx)
    parts = path.rstrip("/").split("/")

    # /api/public/v1/health
    if method == "GET" and path.rstrip("/") == "/api/public/v1/health":
        return json_resp(
            {"status": "ok", "service": "public-content-api", "version": "v1"}
        )

    # /api/public/v1/articles[/:id]
    if len(parts) >= 5 and parts[4] == "articles":
        # GET /api/public/v1/articles
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = min(int(query.get("limit", ["20"])[0]), 100)
            result = await article_svc.list_published(
                page=page,
                limit=limit,
                tag=query.get("tag", [None])[0],
                search=query.get("search", [None])[0],
                content_type=query.get("content_type", [None])[0],
                sort=query.get("sort", [None])[0],
            )
            return json_resp(result.to_dict())

        # GET /api/public/v1/articles/:id_or_slug
        if method == "GET" and len(parts) == 6:
            article = await article_svc.get_by_id_or_slug(parts[5])
            if not article or article.status != ArticleStatus.PUBLISHED:
                return error("Article not found", 404)
            return json_resp({"article": article.to_dict(Scope.DETAIL)})

        return error("Not found", 404)

    # /api/public/v1/tags
    if method == "GET" and len(parts) == 5 and parts[4] == "tags":
        tags = await tag_svc.list_all()
        return json_resp({"tags": [t.to_dict() for t in tags]})

    return error("Not found", 404)
