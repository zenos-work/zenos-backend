from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.reading_lists.service import ReadingListService


async def handle_reading_lists(request, env, path, method, query, ctx):
    svc = ReadingListService(env, ctx)
    parts = path.rstrip("/").split("/")
    # /api/reading-lists => parts: ['', 'api', 'reading-lists']
    # /api/reading-lists/:id => parts[3]
    # /api/reading-lists/:id/articles/:article_id => parts[4]='articles', parts[5]
    list_id = parts[3] if len(parts) > 3 else None
    sub_resource = parts[4] if len(parts) > 4 else None
    article_id = parts[5] if len(parts) > 5 else None

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # POST /api/reading-lists — create list
    if method == "POST" and not list_id:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            lid = await svc.create_list(
                user_id=uid,
                name=data.get("name", ""),
                description=data.get("description"),
                cover_image_url=data.get("cover_image_url"),
                is_public=data.get("is_public", False),
            )
            return json_resp({"id": lid}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/reading-lists — list user's reading lists
    if method == "GET" and not list_id:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.get_lists(uid, page=page, limit=limit))

    # GET /api/reading-lists/:id — get list with items
    if method == "GET" and list_id and not sub_resource:
        try:
            data = await svc.get_list_with_items(list_id, uid)
            return json_resp(data)
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/reading-lists/:id — update list
    if method == "PUT" and list_id and not sub_resource:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            await svc.update_list(
                list_id=list_id,
                user_id=uid,
                name=data.get("name", ""),
                description=data.get("description"),
                cover_image_url=data.get("cover_image_url"),
                is_public=data.get("is_public", False),
            )
            return json_resp({"status": "updated"})
        except ValueError as e:
            return error(str(e), 404)

    # DELETE /api/reading-lists/:id — delete list
    if method == "DELETE" and list_id and not sub_resource:
        try:
            await svc.delete_list(list_id, uid)
            return json_resp({"status": "deleted"})
        except ValueError as e:
            return error(str(e), 400)

    # POST /api/reading-lists/:id/articles/:article_id — add article
    if method == "POST" and list_id and sub_resource == "articles" and article_id:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            iid = await svc.add_article(
                list_id=list_id,
                article_id=article_id,
                user_id=uid,
                note=data.get("note"),
            )
            return json_resp({"id": iid}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/reading-lists/:id/articles/:article_id — remove article
    if method == "DELETE" and list_id and sub_resource == "articles" and article_id:
        try:
            await svc.remove_article(list_id, article_id, uid)
            return json_resp({"status": "removed"})
        except ValueError as e:
            return error(str(e), 400)

    return error("Not found", 404)
