"""Phase 5 Step 24 — Marketing handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.marketing.service import MarketingService


async def handle_marketing(request, env, path, method, query, ctx):
    svc = MarketingService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Distribution Channels ────────────────────────────────
    if path.startswith("/api/marketing/channels"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/marketing/channels
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"channels": await svc.list_channels(org_id)})
        # GET /api/marketing/channels/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_channel(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/channels
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_channel(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    channel_type=data.get("channel_type", ""),
                    config=data.get("config"),
                    kv_secret_key=data.get("kv_secret_key", ""),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/channels/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_channel(
                    parts[4],
                    name=data.get("name"),
                    channel_type=data.get("channel_type"),
                    config=data.get("config"),
                    is_active=data.get("is_active"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/marketing/channels/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_channel(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Scheduled Publications ───────────────────────────────
    if path.startswith("/api/marketing/scheduled"):
        # GET /api/marketing/scheduled
        if method == "GET" and len(parts) == 4:
            return json_resp({"scheduled": await svc.list_scheduled(uid)})
        # GET /api/marketing/scheduled/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_scheduled(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/scheduled
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_scheduled(
                    article_id=data.get("article_id", ""),
                    scheduled_by=uid,
                    scheduled_at=data.get("scheduled_at", ""),
                    timezone=data.get("timezone", "UTC"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/scheduled/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_scheduled_status(
                    parts[4],
                    status=data.get("status", ""),
                    published_at=data.get("published_at", ""),
                    error_message=data.get("error_message", ""),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/marketing/scheduled/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_scheduled(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Content Distribution Jobs ────────────────────────────
    if path.startswith("/api/marketing/distribution-jobs"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/marketing/distribution-jobs
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_dist_jobs(org_id, page, limit))
        # GET /api/marketing/distribution-jobs/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_dist_job(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/distribution-jobs
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_dist_job(
                    org_id=data.get("org_id", ""),
                    article_id=data.get("article_id", ""),
                    channel_id=data.get("channel_id", ""),
                    distribute_at=data.get("distribute_at", ""),
                    run_id=data.get("run_id", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/distribution-jobs/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_dist_job_status(
                    parts[4],
                    status=data.get("status", ""),
                    external_id=data.get("external_id", ""),
                    external_url=data.get("external_url", ""),
                    error_message=data.get("error_message", ""),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Content Syndication ──────────────────────────────────
    if path.startswith("/api/marketing/syndication"):
        article_id = query.get("article_id", [None])[0]
        # GET /api/marketing/syndication
        if method == "GET" and len(parts) == 4:
            if not article_id:
                return error("article_id required", 400)
            return json_resp({"syndications": await svc.list_syndications(article_id)})
        # POST /api/marketing/syndication
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_syndication(
                    article_id=data.get("article_id", ""),
                    platform=data.get("platform", ""),
                    external_url=data.get("external_url", ""),
                    canonical_back_link=data.get("canonical_back_link", True),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/marketing/syndication/:id
        if method == "DELETE" and len(parts) == 5:
            await svc.delete_syndication(parts[4])
            return json_resp({"deleted": True})
        return error("Not found", 404)

    # ── RSS Feeds ────────────────────────────────────────────
    if path.startswith("/api/marketing/rss-feeds"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/marketing/rss-feeds
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"feeds": await svc.list_rss_feeds(org_id)})
        # GET /api/marketing/rss-feeds/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_rss_feed(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/rss-feeds
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_rss_feed(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    slug=data.get("slug", ""),
                    description=data.get("description", ""),
                    filter_tags=data.get("filter_tags"),
                    filter_authors=data.get("filter_authors"),
                    max_items=data.get("max_items", 50),
                    include_premium=data.get("include_premium", False),
                    is_active=data.get("is_active", True),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/rss-feeds/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_rss_feed(
                    parts[4],
                    name=data.get("name"),
                    description=data.get("description"),
                    filter_tags=data.get("filter_tags"),
                    filter_authors=data.get("filter_authors"),
                    max_items=data.get("max_items"),
                    include_premium=data.get("include_premium"),
                    is_active=data.get("is_active"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/marketing/rss-feeds/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_rss_feed(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Content Repurposing ──────────────────────────────────
    if path.startswith("/api/marketing/repurposing"):
        org_id = query.get("org_id", [None])[0]
        # GET /api/marketing/repurposing
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_repurposing(org_id, page, limit))
        # GET /api/marketing/repurposing/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_repurposing(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/repurposing
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_repurposing(
                    org_id=data.get("org_id", ""),
                    article_id=data.get("article_id", ""),
                    fmt=data.get("format", ""),
                    input_options=data.get("input_options"),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/repurposing/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_repurposing_status(
                    parts[4],
                    status=data.get("status", ""),
                    output_content=data.get("output_content", ""),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        return error("Not found", 404)

    # ── Campaigns ────────────────────────────────────────────
    if path.startswith("/api/marketing/campaigns"):
        org_id = query.get("org_id", [None])[0]

        # Campaign articles sub-resource
        # GET/POST/DELETE /api/marketing/campaigns/:id/articles[/:article_id]
        if len(parts) >= 6 and parts[5] == "articles":
            campaign_id = parts[4]
            if method == "GET":
                articles = await svc.list_campaign_articles(campaign_id)
                return json_resp({"articles": articles})
            if method == "POST":
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                await svc.add_campaign_article(campaign_id, data.get("article_id", ""))
                return json_resp({"added": True}, 201)
            if method == "DELETE" and len(parts) == 7:
                await svc.remove_campaign_article(campaign_id, parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # GET /api/marketing/campaigns
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_campaigns(org_id, page, limit))
        # GET /api/marketing/campaigns/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_campaign(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/marketing/campaigns
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_campaign(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    ctype=data.get("type", "content"),
                    start_date=data.get("start_date", ""),
                    end_date=data.get("end_date", ""),
                    budget_cents=data.get("budget_cents", 0),
                    goal_id=data.get("goal_id", ""),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/marketing/campaigns/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_campaign(
                    parts[4],
                    name=data.get("name"),
                    description=data.get("description"),
                    status=data.get("status"),
                    start_date=data.get("start_date"),
                    end_date=data.get("end_date"),
                    budget_cents=data.get("budget_cents"),
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/marketing/campaigns/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_campaign(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    return error("Not found", 404)
