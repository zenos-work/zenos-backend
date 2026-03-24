from utils.helpers import json_resp, error
from models.common.enums import Scope
from api.search.service import SearchService

_VALID_TYPES = {"articles", "tags", "authors", "all"}


async def handle_search(request, env, path, method, query, ctx):
    if method != "GET":
        return error("Method not allowed", 405)

    q = (query.get("q", [""]) or [""])[0].strip()
    if len(q) < 2:
        return error("q must be at least 2 characters", 400)

    search_type = (query.get("type", ["articles"]) or ["articles"])[0].strip().lower()
    if search_type not in _VALID_TYPES:
        return error(f"type must be one of: {', '.join(sorted(_VALID_TYPES))}", 400)

    page = 1
    try:
        page = max(1, int((query.get("page", ["1"]) or ["1"])[0]))
    except (ValueError, TypeError):
        pass

    status = (query.get("status", ["PUBLISHED"]) or ["PUBLISHED"])[0].strip().upper()
    content_type = (query.get("content_type", [None]) or [None])[0]
    outcome_tag = (query.get("outcome_tag", [None]) or [None])[0]
    verified_only_raw = (query.get("verified_only", ["false"]) or ["false"])[0]
    verified_only = str(verified_only_raw).strip().lower() in {"1", "true", "yes"}

    svc = SearchService(env, ctx)

    if search_type == "articles":
        result = await svc.search_articles(
            q,
            page,
            status=status,
            content_type=content_type,
            outcome_tag=outcome_tag,
            verified_only=verified_only,
        )
        return json_resp(result.to_dict(Scope.LIST))

    if search_type == "tags":
        result = await svc.search_tags(q, page)
        return json_resp(result.to_dict())

    if search_type == "authors":
        result = await svc.search_authors(q, page)
        return json_resp(result.to_dict(Scope.PUBLIC))

    # type == "all"
    result = await svc.search_all(
        q,
        status=status,
        content_type=content_type,
        outcome_tag=outcome_tag,
        verified_only=verified_only,
    )
    return json_resp(_serialize_all(result))


def _serialize_all(result: dict) -> dict:
    """Convert model instances inside the 'all' result to plain dicts."""
    from models.base import BaseModel

    def serialize_items(items: list, scope: str) -> list:
        return [i.to_dict(scope) if isinstance(i, BaseModel) else i for i in items]

    return {
        "query": result["query"],
        "articles": {
            "items": serialize_items(result["articles"]["items"], Scope.LIST),
            "total": result["articles"]["total"],
        },
        "tags": {
            "items": serialize_items(result["tags"]["items"], "default"),
            "total": result["tags"]["total"],
        },
        "authors": {
            "items": serialize_items(result["authors"]["items"], Scope.PUBLIC),
            "total": result["authors"]["total"],
        },
    }
