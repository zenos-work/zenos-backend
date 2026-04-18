"""Phase 9 Step 33 — Marketplace handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.marketplace.service import MarketplaceService


async def handle_marketplace(request, env, path, method, query, ctx):
    svc = MarketplaceService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Purchases sub-resource ───────────────────────────────
    # /api/marketplace/:iid/purchases
    if len(parts) >= 5 and parts[4] == "purchases":
        item_id = parts[3]
        if method == "GET":
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_item_purchases(item_id, page, limit))
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.purchase_item(
                    item_id=item_id,
                    buyer_id=uid,
                    org_id=data.get("org_id", ""),
                    payment_id=data.get("payment_id", ""),
                    price_paid_cents=data.get("price_paid_cents", 0),
                    currency=data.get("currency", "USD"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 409)
        return error("Not found", 404)

    # ── Reviews sub-resource ─────────────────────────────────
    # /api/marketplace/:iid/reviews[/:rid]
    if len(parts) >= 5 and parts[4] == "reviews":
        item_id = parts[3]
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_reviews(item_id, page, limit))
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_review(
                    item_id=item_id,
                    reviewer_id=uid,
                    rating=data.get("rating", 0),
                    body=data.get("body", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 409)
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_review(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Publish action ───────────────────────────────────────
    # POST /api/marketplace/:iid/publish
    if len(parts) == 5 and parts[4] == "publish" and method == "POST":
        try:
            return json_resp(await svc.publish_item(parts[3]))
        except ValueError as e:
            return error(str(e), 404)

    # ── My purchases ─────────────────────────────────────────
    # GET /api/marketplace/my-purchases
    if len(parts) == 4 and parts[3] == "my-purchases" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_purchases(uid, page, limit))

    # ── Items CRUD ───────────────────────────────────────────
    # GET /api/marketplace
    if method == "GET" and len(parts) == 3:
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        category = query.get("category", [None])[0]
        seller_id = query.get("seller_id", [None])[0]
        return json_resp(
            await svc.list_items(page, limit, category=category, seller_id=seller_id)
        )
    # POST /api/marketplace
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_item(
                seller_id=uid,
                name=data.get("name", ""),
                slug=data.get("slug", ""),
                short_desc=data.get("short_desc", ""),
                category=data.get("category", ""),
                org_id=data.get("org_id", ""),
                long_desc=data.get("long_desc", ""),
                item_type=data.get("item_type", ""),
                price_cents=data.get("price_cents", 0),
                currency=data.get("currency", "USD"),
                pricing_model=data.get("pricing_model", "one_time"),
                preview_images=data.get("preview_images"),
                asset_url=data.get("asset_url", ""),
                workflow_id=data.get("workflow_id", ""),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)
    # GET /api/marketplace/:iid
    if method == "GET" and len(parts) == 4:
        try:
            return json_resp(await svc.get_item(parts[3]))
        except ValueError as e:
            return error(str(e), 404)
    # PUT /api/marketplace/:iid
    if method == "PUT" and len(parts) == 4:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            return json_resp(await svc.update_item(parts[3], **data))
        except ValueError as e:
            return error(str(e), 404)
    # DELETE /api/marketplace/:iid
    if method == "DELETE" and len(parts) == 4:
        try:
            await svc.delete_item(parts[3])
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
