"""Phase 6 Steps 26-28 — Analytics handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.analytics.service import AnalyticsService


async def handle_analytics(request, env, path, method, query, ctx):
    svc = AnalyticsService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ── Dashboard (Steps 27-28) ──────────────────────────────
    if path.startswith("/api/analytics/dashboard"):
        org_id = query.get("org_id", [None])[0]
        start = query.get("start", [None])[0]
        end = query.get("end", [None])[0]
        if not org_id:
            return error("org_id required", 400)

        # GET /api/analytics/dashboard/events
        if path.endswith("/events") and method == "GET":
            if not start or not end:
                return error("start and end required", 400)
            return json_resp(
                {"breakdown": await svc.dashboard_event_breakdown(org_id, start, end)}
            )

        # GET /api/analytics/dashboard/conversions
        if path.endswith("/conversions") and method == "GET":
            if not start or not end:
                return error("start and end required", 400)
            return json_resp(
                {
                    "conversions": await svc.dashboard_conversion_summary(
                        org_id, start, end
                    )
                }
            )

        # GET /api/analytics/dashboard/experiments
        if path.endswith("/experiments") and method == "GET":
            return json_resp(
                {"experiments": await svc.dashboard_experiment_summary(org_id)}
            )

        return error("Not found", 404)

    # ── Conversion Goals ─────────────────────────────────────
    if path.startswith("/api/analytics/goals"):
        org_id = query.get("org_id", [None])[0]

        # Conversions sub-resource: /api/analytics/goals/:gid/conversions
        if len(parts) >= 6 and parts[5] == "conversions":
            goal_id = parts[4]
            if method == "GET":
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["50"])[0])
                return json_resp(await svc.list_conversions(goal_id, page, limit))
            if method == "POST":
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.record_conversion(
                        goal_id,
                        data.get("org_id", ""),
                        user_id=data.get("user_id", ""),
                        anonymous_id=data.get("anonymous_id", ""),
                        session_id=data.get("session_id", ""),
                        event_id=data.get("event_id", ""),
                        value_cents=data.get("value_cents", 0),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            return error("Not found", 404)

        # GET /api/analytics/goals
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"goals": await svc.list_goals(org_id)})
        # GET /api/analytics/goals/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_goal(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/analytics/goals
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_goal(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    goal_type=data.get("goal_type", ""),
                    target_event_category=data.get("target_event_category", ""),
                    target_event_action=data.get("target_event_action", ""),
                    target_resource_id=data.get("target_resource_id", ""),
                    value_cents=data.get("value_cents", 0),
                    is_active=data.get("is_active", True),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/analytics/goals/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_goal(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/analytics/goals/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_goal(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Funnels ──────────────────────────────────────────────
    if path.startswith("/api/analytics/funnels"):
        org_id = query.get("org_id", [None])[0]

        # Steps sub-resource: /api/analytics/funnels/:fid/steps[/:sid]
        if len(parts) >= 6 and parts[5] == "steps":
            funnel_id = parts[4]
            if method == "GET":
                return json_resp({"steps": await svc.list_funnel_steps(funnel_id)})
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_funnel_step(
                        funnel_id,
                        step_number=data.get("step_number", 0),
                        name=data.get("name", ""),
                        event_category=data.get("event_category", ""),
                        event_action=data.get("event_action", ""),
                        resource_type=data.get("resource_type", ""),
                        resource_id=data.get("resource_id", ""),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "DELETE" and len(parts) == 7:
                await svc.delete_funnel_step(parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # GET /api/analytics/funnels
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"funnels": await svc.list_funnels(org_id)})
        # GET /api/analytics/funnels/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_funnel(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/analytics/funnels
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_funnel(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    description=data.get("description", ""),
                    is_active=data.get("is_active", True),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/analytics/funnels/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_funnel(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/analytics/funnels/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_funnel(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── A/B Experiments ──────────────────────────────────────
    if path.startswith("/api/analytics/experiments"):
        org_id = query.get("org_id", [None])[0]

        # Variants sub-resource: /api/analytics/experiments/:eid/variants[/:vid]
        if len(parts) >= 6 and parts[5] == "variants":
            experiment_id = parts[4]
            if method == "GET" and len(parts) == 6:
                return json_resp({"variants": await svc.list_variants(experiment_id)})
            if method == "POST" and len(parts) == 6:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.create_variant(
                        experiment_id,
                        name=data.get("name", ""),
                        description=data.get("description", ""),
                        changes=data.get("changes"),
                    )
                    return json_resp(result, 201)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "PUT" and len(parts) == 7:
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                try:
                    result = await svc.update_variant_stats(
                        parts[6],
                        data.get("impressions", 0),
                        data.get("conversions", 0),
                    )
                    return json_resp(result)
                except ValueError as e:
                    return error(str(e), 400)
            if method == "DELETE" and len(parts) == 7:
                await svc.delete_variant(parts[6])
                return json_resp({"deleted": True})
            return error("Not found", 404)

        # Assignments sub-resource: /api/analytics/experiments/:eid/assign
        if len(parts) >= 6 and parts[5] == "assign":
            experiment_id = parts[4]
            if method == "POST":
                body = await request.json()
                data = body if isinstance(body, dict) else {}
                result = await svc.get_or_assign(
                    experiment_id,
                    data.get("anonymous_id", ""),
                    data.get("variant_id", ""),
                )
                return json_resp(result)
            return error("Not found", 404)

        # GET /api/analytics/experiments
        if method == "GET" and len(parts) == 4:
            if not org_id:
                return error("org_id required", 400)
            return json_resp({"experiments": await svc.list_experiments(org_id)})
        # GET /api/analytics/experiments/:id
        if method == "GET" and len(parts) == 5:
            try:
                return json_resp(await svc.get_experiment(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        # POST /api/analytics/experiments
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_experiment(
                    org_id=data.get("org_id", ""),
                    name=data.get("name", ""),
                    hypothesis=data.get("hypothesis", ""),
                    traffic_split=data.get("traffic_split"),
                    success_goal_id=data.get("success_goal_id", ""),
                    created_by=uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)
        # PUT /api/analytics/experiments/:id
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_experiment(parts[4], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)
        # DELETE /api/analytics/experiments/:id
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_experiment(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # ── Analytics Events ─────────────────────────────────────
    org_id = query.get("org_id", [None])[0]

    # GET /api/analytics/events
    if path.startswith("/api/analytics/events") and method == "GET":
        if not org_id:
            return error("org_id required", 400)
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["50"])[0])
        return json_resp(await svc.list_analytics_events(org_id, page, limit))

    # POST /api/analytics/events
    if path.startswith("/api/analytics/events") and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.track_event(
                org_id=data.get("org_id", ""),
                event_category=data.get("event_category", ""),
                event_action=data.get("event_action", ""),
                **{
                    k: v
                    for k, v in data.items()
                    if k not in ("org_id", "event_category", "event_action")
                },
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    return error("Not found", 404)
