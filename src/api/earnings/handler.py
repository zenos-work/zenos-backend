from utils.helpers import json_resp, error
from middleware.auth import get_user
from middleware.auth import require_role
from api.earnings.service import EarningsService


async def handle_earnings(request, env, path, method, query, ctx):
    svc = EarningsService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # GET /api/earnings/me
    if path.rstrip("/") == "/api/earnings/me" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.get_earnings(uid, page=page, limit=limit))

    # GET /api/earnings/me/payouts
    if path.rstrip("/") == "/api/earnings/me/payouts" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.get_payouts(uid, page=page, limit=limit))

    # POST /api/earnings/me/payouts/request
    if path.rstrip("/") == "/api/earnings/me/payouts/request" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            pid = await svc.request_payout(
                author_id=uid,
                amount_cents=data.get("amount_cents", 0),
                currency=data.get("currency", "USD"),
                payout_method=data.get("payout_method", "stripe"),
                period_start=data.get("period_start"),
                period_end=data.get("period_end"),
            )
            return json_resp({"id": pid, "status": "pending"}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # POST /api/tips/:article_id
    if path.startswith("/api/tips") and method == "POST":
        article_id = parts[3] if len(parts) > 3 else None
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            tid = await svc.send_tip(
                tipper_id=uid,
                author_id=data.get("author_id", ""),
                amount_cents=data.get("amount_cents", 0),
                article_id=article_id,
                currency=data.get("currency", "USD"),
                message=data.get("message"),
                is_anonymous=data.get("is_anonymous", False),
            )
            return json_resp({"id": tid, "status": "completed"}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/tips/me/received
    if path.rstrip("/") == "/api/tips/me/received" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.get_tips_received(uid, page=page, limit=limit))

    # POST /api/admin/earnings/calculate
    if path.rstrip("/") == "/api/admin/earnings/calculate" and method == "POST":
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.calculate_monthly_distribution(
                period_start=data.get("period_start", ""),
                period_end=data.get("period_end", ""),
                active_subscribers=int(data.get("active_subscribers", 0) or 0),
                payout_ratio=float(data.get("payout_ratio", 0.70) or 0.70),
                min_payout_cents=int(data.get("min_payout_cents", 2500) or 2500),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/admin/earnings/period/:period_start
    if path.startswith("/api/admin/earnings/period/") and method == "GET":
        if not require_role(user, ("SUPERADMIN",)):
            return error("Forbidden", 403)
        period_start = parts[5] if len(parts) > 5 else ""
        return json_resp(await svc.distribution_report(period_start))

    # GET /api/earnings/me/breakdown?period_start=YYYY-MM-01
    if path.rstrip("/") == "/api/earnings/me/breakdown" and method == "GET":
        period_start = query.get("period_start", [""])[0] if query else ""
        return json_resp(await svc.my_breakdown(uid, period_start))

    return error("Not found", 404)
