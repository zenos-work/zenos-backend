"""Phase 7 Step 30 — Publication handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.publications.service import PublicationService


async def handle_publications(request, env, path, method, query, ctx):
    svc = PublicationService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Subscriptions top-level ──────────────────────────────
    # /api/publications/subscriptions[/:sid]
    if len(parts) >= 4 and parts[3] == "subscriptions":
        # GET /api/publications/subscriptions
        if method == "GET" and len(parts) == 4:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_subscriptions(page, limit))
        # POST /api/publications/subscriptions
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_subscription(
                    email=data.get("email", ""),
                    source=data.get("source", "web"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/publications/subscriptions/:sid
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_subscription(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/publications/subscriptions/:sid
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_subscription_status(
                        parts[4], data.get("status", "")
                    )
                )
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/publications/subscriptions/:sid
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_subscription(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Issue Items sub-resource ─────────────────────────────
    # /api/publications/issues/:iid/items[/:item_id]
    if len(parts) >= 6 and parts[3] == "issues" and parts[5] == "items":
        issue_id = parts[4]
        # GET /api/publications/issues/:iid/items
        if method == "GET" and len(parts) == 6:
            return json_resp({"items": await svc.list_items(issue_id)})
        # POST /api/publications/issues/:iid/items
        if method == "POST" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_item(
                    issue_id=issue_id,
                    article_id=data.get("article_id", ""),
                    section=data.get("section", "features"),
                    position=data.get("position", 0),
                    item_type=data.get("item_type", "article"),
                    title=data.get("title", ""),
                    excerpt=data.get("excerpt", ""),
                    include_full_content=data.get("include_full_content", True),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/publications/issues/:iid/items/:item_id
        if method == "GET" and len(parts) == 7:
            try:
                return json_resp(await svc.get_item(parts[6]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/publications/issues/:iid/items/:item_id
        if method == "PUT" and len(parts) == 7:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_item(parts[6], **data))
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/publications/issues/:iid/items/:item_id
        if method == "DELETE" and len(parts) == 7:
            try:
                await svc.delete_item(parts[6])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Generation Runs sub-resource ─────────────────────────
    # /api/publications/issues/:iid/runs[/:rid]
    if len(parts) >= 6 and parts[3] == "issues" and parts[5] == "runs":
        issue_id = parts[4]
        # GET /api/publications/issues/:iid/runs
        if method == "GET" and len(parts) == 6:
            return json_resp({"runs": await svc.list_gen_runs(issue_id)})
        # POST /api/publications/issues/:iid/runs
        if method == "POST" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_gen_run(
                    issue_id=issue_id,
                    job_name=data.get("job_name", ""),
                    trigger_source=data.get("trigger_source", "manual"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/publications/issues/:iid/runs/:rid
        if method == "PUT" and len(parts) == 7:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_gen_run(
                        parts[6],
                        status=data.get("status", ""),
                        error_text=data.get("error_text", ""),
                        metrics_json=data.get("metrics_json"),
                    )
                )
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Deliveries sub-resource ──────────────────────────────
    # /api/publications/issues/:iid/deliveries[/:did]
    if len(parts) >= 6 and parts[3] == "issues" and parts[5] == "deliveries":
        issue_id = parts[4]
        # GET /api/publications/issues/:iid/deliveries
        if method == "GET" and len(parts) == 6:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_deliveries(issue_id, page, limit))
        # POST /api/publications/issues/:iid/deliveries
        if method == "POST" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_delivery(
                    issue_id=issue_id,
                    email=data.get("email", ""),
                    channel=data.get("channel", "email"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/publications/issues/:iid/deliveries/:did
        if method == "PUT" and len(parts) == 7:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_delivery_status(
                        parts[6],
                        status=data.get("status", ""),
                        provider=data.get("provider", ""),
                        provider_message_id=data.get("provider_message_id", ""),
                        error_text=data.get("error_text", ""),
                    )
                )
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Issue approve / publish actions ──────────────────────
    # POST /api/publications/issues/:iid/approve
    if len(parts) == 6 and parts[3] == "issues" and parts[5] == "approve":
        if method == "POST":
            try:
                return json_resp(await svc.approve_issue(parts[4], uid))
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # POST /api/publications/issues/:iid/publish
    if len(parts) == 6 and parts[3] == "issues" and parts[5] == "publish":
        if method == "POST":
            try:
                return json_resp(await svc.publish_issue(parts[4]))
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Publication Issue CRUD ───────────────────────────────
    # /api/publications/issues[/:iid]
    if len(parts) >= 4 and parts[3] == "issues":
        # GET /api/publications/issues
        if method == "GET" and len(parts) == 4:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            issue_type = query.get("issue_type", [None])[0]
            return json_resp(await svc.list_issues(page, limit, issue_type))
        # POST /api/publications/issues
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_issue(
                    issue_type=data.get("issue_type", "magazine"),
                    title=data.get("title", ""),
                    slug=data.get("slug", ""),
                    period_start=data.get("period_start", ""),
                    period_end=data.get("period_end", ""),
                    status=data.get("status", "draft"),
                    editorial_preface=data.get("editorial_preface", ""),
                    toc_json=data.get("toc_json"),
                    cover_article_id=data.get("cover_article_id", ""),
                    created_by_user_id=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/publications/issues/:iid
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_issue(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/publications/issues/:iid
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_issue(parts[4], **data))
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/publications/issues/:iid
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_issue(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    return error("Not found", 404)
