"""Phase 9 Step 34 — Referral handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.referrals.service import ReferralService


async def handle_referrals(request, env, path, method, query, ctx):
    svc = ReferralService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # POST /api/referrals/track  (track a referral event)
    if len(parts) == 4 and parts[3] == "track" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.track_event(
                code=data.get("code", ""),
                event_type=data.get("event_type", "click"),
                referred_user_id=data.get("referred_user_id", ""),
                metadata=data.get("metadata"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/referrals/events
    if len(parts) == 4 and parts[3] == "events" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        try:
            return json_resp(await svc.list_events(uid, page, limit))
        except ValueError as e:
            return error(str(e), 404)

    # GET /api/referrals/stats
    if len(parts) == 4 and parts[3] == "stats" and method == "GET":
        try:
            return json_resp(await svc.get_stats(uid))
        except ValueError as e:
            return error(str(e), 404)

    # POST /api/referrals  (generate / get my referral code)
    if method == "POST" and len(parts) == 3:
        return json_resp(await svc.get_or_create_code(uid), 201)

    # GET /api/referrals  (get my referral code)
    if method == "GET" and len(parts) == 3:
        try:
            return json_resp(await svc.get_stats(uid))
        except ValueError as e:
            return error(str(e), 404)

    return error("Not found", 404)
