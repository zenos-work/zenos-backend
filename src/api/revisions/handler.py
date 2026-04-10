from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.revisions.service import RevisionService


async def handle_revisions(request, env, path, method, query, ctx):
    svc = RevisionService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/articles/:id/revisions => parts: ['', 'api', 'articles', ':id', 'revisions']
    # /api/articles/:id/revisions/:version => parts[5] = version
    article_id = parts[3] if len(parts) > 3 else None
    version = parts[5] if len(parts) > 5 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    # GET /api/articles/:id/revisions
    if method == "GET" and not version:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_revisions(article_id, page=page, limit=limit))

    # GET /api/articles/:id/revisions/:version
    if method == "GET" and version:
        try:
            data = await svc.get_revision(article_id, int(version))
            return json_resp(data)
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
