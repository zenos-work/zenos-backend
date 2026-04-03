from utils.helpers import json_resp, error
from middleware.auth import get_user
from models.series.requests import (
    SeriesCreateRequest,
    SeriesUpdateRequest,
    ArticleSeriesAssignRequest,
)
from api.series.service import SeriesService


async def handle_series(request, env, path, method, query, ctx):
    """Route all /api/series/* requests."""
    svc = SeriesService(env, ctx)
    user = await get_user(request, env)

    if not user:
        return error("Unauthorized", 401)

    user_id = user["sub"]
    parts = path.rstrip("/").split("/")
    series_id = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None

    # POST /api/series (create series)
    if method == "POST" and not series_id:
        try:
            body = await request.json()
            req = SeriesCreateRequest.from_body(body)
            series = await svc.create(user_id, req)
            return json_resp({"series": series.to_dict()}, env=env, request=request)
        except ValueError as e:
            return error(str(e), 400, env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # GET /api/series (list author's series)
    if method == "GET" and not series_id:
        try:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            limit = min(limit, 100)
            result = await svc.list_by_author(user_id, page, limit)
            return json_resp(result.to_dict(), env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # GET /api/series/:id (get series details)
    if method == "GET" and series_id and not action:
        try:
            series = await svc.get_by_id(series_id)
            if not series:
                return error("Series not found", 404, env=env, request=request)
            return json_resp({"series": series.to_dict()}, env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # GET /api/series/:id/articles (get articles in series)
    if method == "GET" and series_id and action == "articles":
        try:
            series = await svc.get_by_id(series_id)
            if not series:
                return error("Series not found", 404, env=env, request=request)
            articles = await svc.list_series_articles(series_id)
            return json_resp(
                {
                    "series": series.to_dict(),
                    "articles": [a.to_dict() for a in articles],
                },
                env=env,
                request=request,
            )
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # PUT /api/series/:id (update series)
    if method == "PUT" and series_id and not action:
        try:
            body = await request.json()
            req = SeriesUpdateRequest.from_body(body)
            series = await svc.update(series_id, user_id, req)
            if not series:
                return error(
                    "Series not found or not authorized", 404, env=env, request=request
                )
            return json_resp({"series": series.to_dict()}, env=env, request=request)
        except ValueError as e:
            return error(str(e), 400, env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # DELETE /api/series/:id (delete series)
    if method == "DELETE" and series_id and not action:
        try:
            success = await svc.delete(series_id, user_id)
            if not success:
                return error(
                    "Series not found or not authorized", 404, env=env, request=request
                )
            return json_resp({"message": "Series deleted"}, env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # POST /api/series/:id/articles/:article_id (assign article to series)
    if method == "POST" and series_id and action == "articles":
        try:
            article_id = parts[5] if len(parts) > 5 else None
            if not article_id:
                return error("Article ID required", 400, env=env, request=request)

            body = await request.json()
            req = ArticleSeriesAssignRequest.from_body(body)
            success = await svc.assign_article(article_id, series_id, user_id, req)
            if not success:
                return error(
                    "Article or series not found or not authorized",
                    404,
                    env=env,
                    request=request,
                )
            return json_resp(
                {"message": "Article assigned to series"}, env=env, request=request
            )
        except ValueError as e:
            return error(str(e), 400, env=env, request=request)
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    # DELETE /api/series/:id/articles/:article_id (remove article from series)
    if method == "DELETE" and series_id and action == "articles":
        try:
            article_id = parts[5] if len(parts) > 5 else None
            if not article_id:
                return error("Article ID required", 400, env=env, request=request)

            success = await svc.remove_article(article_id, series_id, user_id)
            if not success:
                return error(
                    "Series not found or not authorized", 404, env=env, request=request
                )
            return json_resp(
                {"message": "Article removed from series"}, env=env, request=request
            )
        except Exception as e:
            return error(
                f"Internal server error: {str(e)}", 500, env=env, request=request
            )

    return error("Not found", 404, env=env, request=request)
