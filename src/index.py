from workers import WorkerEntrypoint
from urllib.parse import urlparse, parse_qs
from middleware.logging import with_logging
from utils.helpers import json_resp, cors_headers
from auth.router import handle_auth

# Import all API handlers (add as you build each module)
from api.articles.handler import handle_articles
from api.users.handler import handle_users
from api.tags.handler import handle_tags
from api.comments.handler import handle_comments
from api.social.handler import handle_social
from api.feed.handler import handle_feed
from api.media.handler import handle_media
from api.admin.handler import handle_admin
from api.search.handler import handle_search

from js import Response


class Default(WorkerEntrypoint):
    async def on_fetch(self, request):
        return await with_logging(request, self.env, self._dispatch)

    async def _dispatch(self, ctx):
        """Pure routing — no business logic here."""
        request = ctx.request
        env = ctx.env
        url = urlparse(request.url)
        path = url.path
        method = request.method
        query = parse_qs(url.query)

        if method == "OPTIONS":
            return Response.new(
                None,
                status=204,
                headers=cors_headers(
                    env=env,
                    request=request,
                    content_type=None,
                    allow_credentials=True,
                ),
            )

        if path == "/health":
            return json_resp(
                {
                    "status": "ok",
                    "service": "zenos-api",
                    "env": env.ENVIRONMENT,
                    "trace_id": ctx.trace_id,
                },
                env=env,
                request=request,
            )

        if path.startswith("/auth/"):
            return await handle_auth(request, env, path)

        if path.startswith("/api/articles"):
            return await handle_articles(request, env, path, method, query, ctx)
        if path.startswith("/api/users"):
            return await handle_users(request, env, path, method, query, ctx)
        if path.startswith("/api/tags"):
            return await handle_tags(request, env, path, method, query, ctx)
        if path.startswith("/api/comments"):
            return await handle_comments(request, env, path, method, query, ctx)
        if path.startswith("/api/social"):
            return await handle_social(request, env, path, method, query, ctx)
        if path.startswith("/api/feed"):
            return await handle_feed(request, env, path, method, query, ctx)
        if path.startswith("/api/media"):
            return await handle_media(request, env, path, method, query, ctx)
        if path.startswith("/api/admin"):
            return await handle_admin(request, env, path, method, query, ctx)

        if path.startswith("/api/search"):
            return await handle_search(request, env, path, method, query, ctx)

        return json_resp({"error": "Not found"}, 404, env=env, request=request)
