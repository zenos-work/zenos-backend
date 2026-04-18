from utils.helpers import json_resp, error
from middleware.auth import get_user, require_role
from api.reports.service import ReportService


async def handle_reports(request, env, path, method, query, ctx):
    svc = ReportService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # POST /api/reports — submit a report (any authenticated user)
    if path.rstrip("/") == "/api/reports" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            rid = await svc.submit_report(
                reporter_id=uid,
                resource_type=data.get("resource_type", ""),
                resource_id=data.get("resource_id", ""),
                reason=data.get("reason", ""),
                org_id=data.get("org_id"),
                detail_text=data.get("detail_text"),
            )
            return json_resp({"id": rid, "status": "pending"}, 201)
        except ValueError as e:
            return error(str(e), 400)

    # GET /api/admin/reports — list reports (APPROVER+)
    if path.startswith("/api/admin/reports") and method == "GET":
        if not require_role(user, ["APPROVER", "SUPERADMIN"]):
            return error("Forbidden", 403)
        # /api/admin/reports/:id — single report
        report_id = parts[4] if len(parts) > 4 else None
        if report_id:
            report = await svc._repo.find_by_id(report_id)
            if not report:
                return error("Report not found", 404)
            return json_resp(report.to_dict(scope="admin"))

        status_filter = query.get("status", [None])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(
            await svc.list_reports(status=status_filter, page=page, limit=limit)
        )

    # PUT /api/admin/reports/:id — review/resolve (APPROVER+)
    if path.startswith("/api/admin/reports") and method == "PUT":
        if not require_role(user, ["APPROVER", "SUPERADMIN"]):
            return error("Forbidden", 403)
        report_id = parts[4] if len(parts) > 4 else None
        if not report_id:
            return error("Report ID required", 400)
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.review_report(
                report_id=report_id,
                reviewer_id=uid,
                status=data.get("status", ""),
                action_taken=data.get("action_taken"),
                action_note=data.get("action_note"),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    return error("Not found", 404)
