"""Membership and premium endpoints for Phase 3"""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.membership.service import MembershipService


async def handle_membership(request, env, path, method, query, ctx):
    """Handle membership and premium-related endpoints."""
    svc = MembershipService(env, ctx)
    parts = path.rstrip("/").split("/")
    resource = parts[3] if len(parts) > 3 else None
    action = parts[4] if len(parts) > 4 else None

    # GET /api/membership/plans - Get all plans (no auth required)
    if method == "GET" and resource == "plans" and not action:
        try:
            plans = await svc.get_membership_plans()
            return json_resp({"plans": plans})
        except Exception as e:
            await ctx.log.error(f"Error fetching plans: {e}")
            return error("Failed to fetch plans", 500)

    # GET /api/membership/me - Get current user's membership (auth required)
    if method == "GET" and resource == "me":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        try:
            membership = await svc.get_user_membership(user["sub"])
            if not membership:
                return error("User membership not found", 404)
            return json_resp({"membership": membership})
        except Exception as e:
            await ctx.log.error(f"Error fetching user membership: {e}")
            return error("Failed to fetch membership", 500)

    # POST /api/membership/upgrade - Upgrade membership (for testing)
    if method == "POST" and resource == "upgrade":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        try:
            body = await request.json()
            new_tier = body.get("tier")
            stripe_subscription_id = body.get("stripe_subscription_id")

            if not new_tier or new_tier not in ("free", "creator_pro", "team_suite"):
                return error("Invalid membership tier", 400)

            result = await svc.upgrade_membership(
                user["sub"], new_tier, stripe_subscription_id
            )
            return json_resp(result, 201)
        except Exception as e:
            await ctx.log.error(f"Error upgrading membership: {e}")
            return error("Failed to upgrade membership", 500)

    # POST /api/membership/premium-read - Track premium article read
    if method == "POST" and resource == "premium-read":
        user = await get_user(request, env)
        if not user:
            return error("Unauthorised", 401)

        try:
            body = await request.json()
            article_id = body.get("article_id")
            scroll_depth = float(body.get("scroll_depth", 0))
            duration_seconds = int(body.get("duration_seconds", 0))

            if not article_id:
                return error("article_id is required", 400)

            result = await svc.track_premium_read(
                user["sub"],
                article_id,
                scroll_depth,
                duration_seconds,
            )
            return json_resp(result, 201)
        except Exception as e:
            await ctx.log.error(f"Error tracking premium read: {e}")
            return error("Failed to track premium read", 500)

    # POST /api/membership/funnel-event - Log conversion funnel event
    if method == "POST" and resource == "funnel-event":
        user = await get_user(request, env)
        # user can be None for anonymous events

        try:
            body = await request.json()
            event_type = body.get("event_type")
            article_id = body.get("article_id")
            device_type = body.get("device_type")
            referrer = body.get("referrer")
            ip_hash = body.get("ip_hash")

            if not event_type:
                return error("event_type is required", 400)

            result = await svc.log_premium_funnel_event(
                event_type=event_type,
                article_id=article_id,
                user_id=user.get("sub") if user else None,
                device_type=device_type,
                referrer=referrer,
                ip_hash=ip_hash,
            )
            return json_resp(result, 201)
        except Exception as e:
            await ctx.log.error(f"Error logging funnel event: {e}")
            return error("Failed to log funnel event", 500)

    return error("Not found", 404)
