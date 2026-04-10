"""Phase 7 Step 29 — Newsletter handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.newsletters.service import NewsletterService


async def handle_newsletters(request, env, path, method, query, ctx):
    svc = NewsletterService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Subscribers sub-resource ─────────────────────────────
    # /api/newsletters/:nid/subscribers[/:sid]
    if len(parts) >= 5 and parts[4] == "subscribers":
        newsletter_id = parts[3]
        # GET /api/newsletters/:nid/subscribers
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_subscribers(newsletter_id, page, limit))
        # POST /api/newsletters/:nid/subscribers
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_subscriber(
                    newsletter_id=newsletter_id,
                    email=data.get("email", ""),
                    first_name=data.get("first_name", ""),
                    last_name=data.get("last_name", ""),
                    source=data.get("source", "web"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/newsletters/:nid/subscribers/:sid
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_subscriber(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/newsletters/:nid/subscribers/:sid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_subscriber_status(parts[5], data.get("status", ""))
                )
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/newsletters/:nid/subscribers/:sid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_subscriber(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Issues sub-resource ──────────────────────────────────
    # /api/newsletters/:nid/issues[/:iid][/articles|/send-events]
    if len(parts) >= 5 and parts[4] == "issues":
        newsletter_id = parts[3]

        # Issue articles sub-sub-resource
        if len(parts) >= 7 and parts[6] == "articles":
            issue_id = parts[5]
            if method == "GET":
                return json_resp({"articles": await svc.list_issue_articles(issue_id)})
            if method == "POST":
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                await svc.add_issue_article(
                    issue_id,
                    data.get("article_id", ""),
                    data.get("sort_order", 0),
                    data.get("blurb", ""),
                )
                return json_resp({"added": True}, 201)
            if method == "DELETE" and len(parts) == 8:
                await svc.remove_issue_article(issue_id, parts[7])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # Send events sub-sub-resource
        if len(parts) >= 7 and parts[6] == "send-events":
            issue_id = parts[5]
            if method == "GET":
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["20"])[0])
                return json_resp(await svc.list_send_events(issue_id, page, limit))
            if method == "POST":
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_send_event(
                        issue_id=issue_id,
                        subscriber_id=data.get("subscriber_id", ""),
                        event_type=data.get("event_type", ""),
                        link_url=data.get("link_url", ""),
                        metadata=data.get("metadata"),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            return error("Not found", 404)

        # Issue status update
        if len(parts) == 7 and parts[6] == "send":
            if method == "POST":
                try:
                    return json_resp(await svc.update_issue_status(parts[5], "sending"))
                except ValueError as e:
                    return error(str(e), 400)
            return error("Not found", 404)

        # GET /api/newsletters/:nid/issues
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_issues(newsletter_id, page, limit))
        # POST /api/newsletters/:nid/issues
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_issue(
                    newsletter_id=newsletter_id,
                    subject=data.get("subject", ""),
                    preview_text=data.get("preview_text", ""),
                    body_html=data.get("body_html", ""),
                    body_text=data.get("body_text", ""),
                    issue_type=data.get("issue_type", "digest"),
                    article_ids=data.get("article_ids"),
                    status=data.get("status", "draft"),
                    scheduled_at=data.get("scheduled_at", ""),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # GET /api/newsletters/:nid/issues/:iid
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_issue(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        # PUT /api/newsletters/:nid/issues/:iid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_issue(parts[5], **data))
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/newsletters/:nid/issues/:iid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_issue(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Segments sub-resource ────────────────────────────────
    # /api/newsletters/:nid/segments[/:sid]
    if len(parts) >= 5 and parts[4] == "segments":
        newsletter_id = parts[3]
        if method == "GET" and len(parts) == 5:
            return json_resp({"segments": await svc.list_segments(newsletter_id)})
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_segment(
                    newsletter_id=newsletter_id,
                    name=data.get("name", ""),
                    filter_rules=data.get("filter_rules"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_segment(parts[5]))
            except ValueError as e:
                return error(str(e), 404)
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(
                    await svc.update_segment(
                        parts[5],
                        name=data.get("name"),
                        filter_rules=data.get("filter_rules"),
                    )
                )
            except ValueError as e:
                return error(str(e), 400)
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_segment(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Newsletter CRUD ──────────────────────────────────────
    # GET /api/newsletters
    if method == "GET" and len(parts) == 3:
        org_id = query.get("org_id", [None])[0]
        if org_id:
            return json_resp({"newsletters": await svc.list_newsletters(org_id)})
        return json_resp({"newsletters": await svc.list_newsletters_by_owner(uid)})
    # POST /api/newsletters
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_newsletter(
                org_id=data.get("org_id", ""),
                owner_id=uid,
                name=data.get("name", ""),
                slug=data.get("slug", ""),
                description=data.get("description", ""),
                logo_url=data.get("logo_url", ""),
                cover_url=data.get("cover_url", ""),
                from_name=data.get("from_name", ""),
                from_email=data.get("from_email", ""),
                reply_to_email=data.get("reply_to_email", ""),
                is_premium_only=data.get("is_premium_only", False),
                membership_tier=data.get("membership_tier", ""),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
    # GET /api/newsletters/:id
    if method == "GET" and len(parts) == 4:
        try:
            return json_resp(await svc.get_newsletter(parts[3]))
        except ValueError as e:
            return error(str(e), 404)
    # PUT /api/newsletters/:id
    if method == "PUT" and len(parts) == 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_newsletter(parts[3], **data))
        except ValueError as e:
            return error(str(e), 400)
    # DELETE /api/newsletters/:id
    if method == "DELETE" and len(parts) == 4:
        try:
            await svc.delete_newsletter(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
