"""Phase 10 Step 37 — Workflow cost handler."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.workflow_costs.service import WorkflowCostService
from api.feature_flags.service import FeatureFlagService


async def _is_feature_enabled(env, ctx, user, flag_key: str) -> bool:
    if getattr(env, "DB", None) is None:
        return True
    try:
        svc = FeatureFlagService(env, ctx)
        return await svc.evaluate_one(
            flag_key,
            user_id=user.get("sub"),
            user_role=user.get("role", ""),
        )
    except Exception:
        return False


async def handle_workflow_costs(request, env, path, method, query, ctx):
    svc = WorkflowCostService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)

    if not await _is_feature_enabled(env, ctx, user, "workflow_costs"):
        return error("Feature 'workflow_costs' is disabled", 403)

    # /api/workflow-costs/rates[/:rid]
    if len(parts) >= 4 and parts[3] == "rates":
        if method == "GET" and len(parts) == 4:
            org_id = query.get("org_id", [""])[0]
            if org_id:
                return json_resp({"rates": await svc.list_rates(org_id)})
            return json_resp({"rates": await svc.list_global_rates()})
        if method == "POST" and len(parts) == 4:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            result = await svc.create_rate(
                org_id=data.get("org_id", ""),
                node_type_id=data.get("node_type_id", ""),
                cost_model=data.get("cost_model", "per_execution"),
                rate_microcents=data.get("rate_microcents", 0),
                unit_label=data.get("unit_label", ""),
                currency=data.get("currency", "USD"),
                notes=data.get("notes", ""),
            )
            return json_resp(result, 201)
        if method == "PUT" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                return json_resp(await svc.update_rate(parts[4], **data))
            except ValueError as e:
                return error(str(e), 404)
        if method == "DELETE" and len(parts) == 5:
            try:
                await svc.delete_rate(parts[4])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # /api/workflow-costs/runs/:run_id
    if len(parts) >= 5 and parts[3] == "runs":
        run_id = parts[4]
        if method == "GET":
            return json_resp({"costs": await svc.list_run_costs(run_id)})
        return error("Not found", 404)

    # /api/workflow-costs/workflows/:wid
    if len(parts) >= 5 and parts[3] == "workflows":
        workflow_id = parts[4]
        if method == "GET":
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_workflow_costs(workflow_id, page, limit))
        return error("Not found", 404)

    # /api/workflow-costs/summaries
    if len(parts) == 4 and parts[3] == "summaries" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        return json_resp({"summaries": await svc.list_cost_summaries(org_id)})

    # /api/workflow-costs/summary/:wid
    if len(parts) == 5 and parts[3] == "summary":
        if method == "GET":
            try:
                return json_resp(await svc.get_cost_summary(parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # /api/workflow-costs/monthly
    if len(parts) == 4 and parts[3] == "monthly" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["12"])[0])
        return json_resp(await svc.list_monthly_rollups(org_id, page, limit))

    # /api/workflow-costs/monthly/:year_month
    if len(parts) == 5 and parts[3] == "monthly":
        org_id = query.get("org_id", [""])[0]
        if method == "GET":
            try:
                return json_resp(await svc.get_monthly_rollup(org_id, parts[4]))
            except ValueError as e:
                return error(str(e), 404)
        return error("Not found", 404)

    # /api/workflow-costs/budget-cap
    if len(parts) == 4 and parts[3] == "budget-cap":
        if method == "PUT":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            return json_resp(
                await svc.set_budget_cap(
                    org_id=data.get("org_id", ""),
                    year_month=data.get("year_month", ""),
                    budget_cap_microcents=data.get("budget_cap_microcents", 0),
                )
            )
        return error("Not found", 404)

    # /api/workflow-costs/budget-check
    if len(parts) == 4 and parts[3] == "budget-check" and method == "GET":
        org_id = query.get("org_id", [""])[0]
        year_month = query.get("year_month", [""])[0]
        return json_resp(await svc.check_budget(org_id, year_month))

    # POST /api/workflow-costs  (record a cost entry)
    if method == "POST" and len(parts) == 3:
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        result = await svc.record_cost(
            run_id=data.get("run_id", ""),
            step_id=data.get("step_id", ""),
            workflow_id=data.get("workflow_id", ""),
            org_id=data.get("org_id", ""),
            node_type_id=data.get("node_type_id", ""),
            cost_model=data.get("cost_model", ""),
            units_consumed=data.get("units_consumed", 0),
            unit_label=data.get("unit_label", ""),
            cost_microcents=data.get("cost_microcents", 0),
            cost_actual_microcents=data.get("cost_actual_microcents", 0),
            currency=data.get("currency", "USD"),
            external_ref=data.get("external_ref", ""),
            notes=data.get("notes", ""),
        )
        return json_resp(result, 201)

    return error("Not found", 404)
