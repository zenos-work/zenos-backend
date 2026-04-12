"""Workflow handler — routing for Steps 20-22."""

from utils.helpers import json_resp, error
from middleware.auth import get_user
from api.workflows.service import WorkflowService


async def handle_workflows(request, env, path, method, query, ctx):
    svc = WorkflowService(env, ctx)
    parts = path.rstrip("/").split("/")

    user = await get_user(request, env)
    if not user:
        return error("Unauthorised", 401)
    uid = user["sub"]

    # ═════════════════════════════════════════════════════════
    # Step 20 — Core builder
    # ═════════════════════════════════════════════════════════

    # ── Node types (read-only catalogue) ──────────────────────
    # GET /api/workflow-node-types
    if path.startswith("/api/workflow-node-types") and method == "GET":
        category = query.get("category", [None])[0]
        types = await svc.list_node_types(category=category)
        return json_resp({"node_types": types})

    # ── Templates (public) ────────────────────────────────────
    # GET /api/workflow-templates
    if path.rstrip("/") == "/api/workflow-templates" and method == "GET":
        category = query.get("category", [None])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(
            await svc.list_templates(category=category, page=page, limit=limit)
        )

    # POST /api/workflow-templates/:id/clone
    if (
        path.startswith("/api/workflow-templates/")
        and path.endswith("/clone")
        and method == "POST"
    ):
        template_id = parts[3]
        org_id = query.get("org_id", [None])[0]
        if not org_id:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            org_id = data.get("org_id", "")
        try:
            result = await svc.clone_from_template(template_id, org_id, uid)
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # ── Human tasks for current user ──────────────────────────
    # GET /api/workflow-tasks
    if path.rstrip("/") == "/api/workflow-tasks" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(await svc.list_tasks(user_id=uid, page=page, limit=limit))

    # GET /api/workflow-tasks/:id
    if path.startswith("/api/workflow-tasks/") and method == "GET":
        task_id = parts[3]
        try:
            return json_resp(await svc.get_task(task_id))
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/workflow-tasks/:id/start
    if (
        path.startswith("/api/workflow-tasks/")
        and path.endswith("/start")
        and method == "PUT"
    ):
        task_id = parts[3]
        try:
            return json_resp(await svc.start_task_review(task_id, uid))
        except ValueError as e:
            return error(str(e), 400)

    # PUT /api/workflow-tasks/:id
    if (
        path.startswith("/api/workflow-tasks/")
        and method == "PUT"
        and not path.endswith("/start")
    ):
        task_id = parts[3]
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.complete_task(
                task_id,
                reviewer_id=uid,
                decision=data.get("decision", ""),
                reviewer_note=data.get("reviewer_note", ""),
                output_data=data.get("output_data"),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # ── Pending approvals for current user ────────────────────
    # GET /api/workflow-approvals
    if path.rstrip("/") == "/api/workflow-approvals" and method == "GET":
        items = await svc.list_pending_approvals(uid)
        return json_resp({"approvals": items})

    # PUT /api/workflow-approvals/:id
    if path.startswith("/api/workflow-approvals/") and method == "PUT":
        approval_id = parts[3]
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.review_approval(
                approval_id,
                reviewed_by=uid,
                action=data.get("action", ""),
                review_note=data.get("review_note", ""),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # ═════════════════════════════════════════════════════════
    # /api/workflows/...  routes
    # ═════════════════════════════════════════════════════════
    if not path.startswith("/api/workflows"):
        return error("Not found", 404)

    # ── List workflows ────────────────────────────────────────
    # GET /api/workflows
    if path.rstrip("/") == "/api/workflows" and method == "GET":
        org_id = query.get("org_id", [None])[0]
        status = query.get("status", [None])[0]
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["20"])[0])
        return json_resp(
            await svc.list_workflows(
                org_id=org_id, owner_id=uid, status=status, page=page, limit=limit
            )
        )

    # POST /api/workflows - create
    if path.rstrip("/") == "/api/workflows" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.create_workflow(
                org_id=data.get("org_id", ""),
                owner_id=uid,
                name=data.get("name", ""),
                description=data.get("description", ""),
                trigger_type=data.get("trigger_type", "manual"),
                environment=data.get("environment", "dev"),
                tags=data.get("tags"),
                scope_type=data.get("scope_type", "manual"),
                scope_filter=data.get("scope_filter"),
                folder_id=data.get("folder_id"),
                approval_required=data.get("approval_required", False),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # ── Extract workflow_id from path ─────────────────────────
    # Pattern: /api/workflows/:wf_id[/sub_resource[/:sub_id[/action]]]
    # parts: ["", "api", "workflows", wf_id, sub, sub_id, action]
    if len(parts) < 4:
        return error("Not found", 404)
    wf_id = parts[3]

    # GET /api/workflows/:id
    if len(parts) == 4 and method == "GET":
        try:
            return json_resp(await svc.get_workflow(wf_id))
        except ValueError as e:
            return error(str(e), 404)

    # PUT /api/workflows/:id
    if len(parts) == 4 and method == "PUT":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.update_workflow(wf_id, updated_by=uid, **data)
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # DELETE /api/workflows/:id
    if len(parts) == 4 and method == "DELETE":
        try:
            await svc.delete_workflow(wf_id, deleted_by=uid)
            return json_resp({"deleted": True})
        except ValueError as e:
            return error(str(e), 404)

    # POST /api/workflows/:id/clone
    if len(parts) == 5 and parts[4] == "clone" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.clone_workflow(
                wf_id,
                uid,
                data.get("org_id", ""),
                data.get("name"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # ── Nodes ─────────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "nodes":
        # POST /api/workflows/:id/nodes
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.add_node(
                    wf_id,
                    data.get("node_type_id", ""),
                    label=data.get("label", ""),
                    position_x=data.get("position_x", 0),
                    position_y=data.get("position_y", 0),
                    display_config=data.get("display_config"),
                    connector_binding_id=data.get("connector_binding_id"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # PUT /api/workflows/:id/nodes/:node_id
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_node(parts[5], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/nodes/:node_id
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_node(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)

    # ── Edges ─────────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "edges":
        # POST /api/workflows/:id/edges
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.add_edge(
                    wf_id,
                    data.get("source_node_id", ""),
                    data.get("target_node_id", ""),
                    data.get("condition_label", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/edges/:edge_id
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_edge(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)

    # ── Versions ──────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "versions":
        # GET /api/workflows/:id/versions
        if method == "GET" and len(parts) == 5:
            return json_resp({"versions": await svc.list_versions(wf_id)})

        # POST /api/workflows/:id/versions
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_version(wf_id, uid, data.get("changelog", ""))
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # POST /api/workflows/:id/versions/:version_number/restore
        if method == "POST" and len(parts) == 7 and parts[6] == "restore":
            try:
                version_number = int(parts[5])
            except Exception:
                return error("Invalid version number", 400)
            try:
                result = await svc.restore_version(
                    wf_id,
                    restored_by=uid,
                    version_number=version_number,
                )
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)

    # POST /api/workflows/:id/restore
    if len(parts) == 5 and parts[4] == "restore" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.restore_version(
                wf_id,
                restored_by=uid,
                version_id=data.get("version_id", ""),
                version_number=int(data.get("version_number", 0) or 0),
            )
            return json_resp(result)
        except ValueError as e:
            return error(str(e), 400)

    # ── Webhooks ──────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "webhooks":
        # GET /api/workflows/:id/webhooks
        if method == "GET" and len(parts) == 5:
            return json_resp({"webhooks": await svc.list_webhooks(wf_id)})

        # POST /api/workflows/:id/webhooks
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_webhook(
                    wf_id, data.get("node_id"), data.get("method", "POST")
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/webhooks/:wh_id
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_webhook(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)

    # ── Publish as template ───────────────────────────────────
    # POST /api/workflows/:id/publish-template
    if len(parts) == 5 and parts[4] == "publish-template" and method == "POST":
        body = await request.json()
        data = body if isinstance(body, dict) else {}
        try:
            result = await svc.publish_template(
                wf_id,
                data.get("title", ""),
                data.get("short_desc", ""),
                data.get("category", ""),
                data.get("use_case_tags"),
                data.get("preview_image"),
            )
            return json_resp(result, 201)
        except ValueError as e:
            return error(str(e), 400)

    # ═════════════════════════════════════════════════════════
    # Step 21 — Runs
    # ═════════════════════════════════════════════════════════

    if len(parts) >= 5 and parts[4] == "runs":
        # GET /api/workflows/:id/runs
        if method == "GET" and len(parts) == 5:
            page = int(query.get("page", ["1"])[0])
            limit = int(query.get("limit", ["20"])[0])
            return json_resp(await svc.list_runs(wf_id, page=page, limit=limit))

        # GET /api/workflows/:id/runs/:run_id
        if method == "GET" and len(parts) == 6:
            try:
                return json_resp(await svc.get_run(parts[5]))
            except ValueError as e:
                return error(str(e), 404)

        # POST /api/workflows/:id/runs (trigger)
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.trigger_run(
                    wf_id,
                    data.get("triggered_by", "manual"),
                    data.get("trigger_payload"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # POST /api/workflows/:id/runs/:run_id/cancel
        if method == "POST" and len(parts) == 7 and parts[6] == "cancel":
            try:
                return json_resp(await svc.cancel_run(parts[5]))
            except ValueError as e:
                return error(str(e), 400)

        # GET /api/workflows/:id/runs/:run_id/costs
        if method == "GET" and len(parts) == 7 and parts[6] == "costs":
            costs = await svc.get_run_costs(parts[5])
            return json_resp({"costs": costs})

        # GET /api/workflows/:id/runs/:run_id/messages
        if method == "GET" and len(parts) == 7 and parts[6] == "messages":
            msgs = await svc.list_messages(parts[5])
            return json_resp({"messages": msgs})

        # POST /api/workflows/:id/runs/:run_id/messages
        if method == "POST" and len(parts) == 7 and parts[6] == "messages":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.add_message(
                    run_id=parts[5],
                    workflow_id=wf_id,
                    sender_id=uid,
                    content=data.get("content", ""),
                    sender_role=data.get("sender_role", "author"),
                    message_type=data.get("message_type", "comment"),
                    step_id=data.get("step_id"),
                    task_id=data.get("task_id"),
                    attachment_url=data.get("attachment_url"),
                    attachment_type=data.get("attachment_type"),
                    is_internal=data.get("is_internal", False),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

    # ═════════════════════════════════════════════════════════
    # Step 22 — Enterprise sub-resources
    # ═════════════════════════════════════════════════════════

    # ── Approvals ─────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "approvals":
        # GET /api/workflows/:id/approvals
        if method == "GET":
            return json_resp({"approvals": await svc.list_approvals(wf_id)})

        # POST /api/workflows/:id/approvals
        if method == "POST":
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.request_approval(
                    wf_id,
                    requested_by=uid,
                    assigned_to=data.get("assigned_to"),
                    request_note=data.get("request_note", ""),
                    expires_at=data.get("expires_at"),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

    # ── Content bindings ──────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "bindings":
        # GET /api/workflows/:id/bindings
        if method == "GET":
            return json_resp({"bindings": await svc.list_bindings(wf_id)})

        # POST /api/workflows/:id/bindings
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_binding(
                    wf_id,
                    data.get("org_id", ""),
                    data.get("bind_type", "all_org_content"),
                    data.get("bind_criteria"),
                    data.get("trigger_event", "on_submit"),
                    data.get("priority", 100),
                    uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # PUT /api/workflows/:id/bindings/:bid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_binding(parts[5], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/bindings/:bid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_binding(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)

    # ── Permissions ───────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "permissions":
        # GET /api/workflows/:id/permissions
        if method == "GET":
            return json_resp({"permissions": await svc.list_permissions(wf_id)})

        # POST /api/workflows/:id/permissions
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.grant_permission(
                    wf_id,
                    data.get("grantee_type", ""),
                    data.get("grantee_id", ""),
                    data.get("permission", ""),
                    uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/permissions/:pid
        if method == "DELETE" and len(parts) == 6:
            await svc.revoke_permission(parts[5])
            return json_resp({"deleted": True})

    # ── Folders ───────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "folders":
        # GET /api/workflows/:id/folders  (org_id from workflow)
        if method == "GET":
            wf = await svc._repo.find_workflow(wf_id)
            if wf:
                return json_resp({"folders": await svc.list_folders(wf.org_id)})
            return json_resp({"folders": []})

    # ── Schedules ─────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "schedules":
        # GET /api/workflows/:id/schedules
        if method == "GET":
            return json_resp({"schedules": await svc.list_schedules(workflow_id=wf_id)})

        # POST /api/workflows/:id/schedules
        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_schedule(
                    data.get("org_id", ""),
                    wf_id,
                    data.get("name", ""),
                    data.get("cron_expression", ""),
                    data.get("timezone", "UTC"),
                    data.get("next_fire_at"),
                    uid,
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

        # PUT /api/workflows/:id/schedules/:sid
        if method == "PUT" and len(parts) == 6:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.update_schedule(parts[5], **data)
                return json_resp(result)
            except ValueError as e:
                return error(str(e), 400)

        # DELETE /api/workflows/:id/schedules/:sid
        if method == "DELETE" and len(parts) == 6:
            try:
                await svc.delete_schedule(parts[5])
                return json_resp({"deleted": True})
            except ValueError as e:
                return error(str(e), 404)

    # ── Audit log ─────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "audit-log" and method == "GET":
        page = int(query.get("page", ["1"])[0])
        limit = int(query.get("limit", ["50"])[0])
        return json_resp(
            await svc.get_audit_log(workflow_id=wf_id, page=page, limit=limit)
        )

    # ── Cost summary ──────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "costs" and method == "GET":
        summary = await svc.get_cost_summary(wf_id)
        return json_resp({"cost_summary": summary})

    # ── Promotions ────────────────────────────────────────────
    if len(parts) >= 5 and parts[4] == "promotions":
        if method == "GET":
            return json_resp({"promotions": await svc.list_promotions(wf_id)})

        if method == "POST" and len(parts) == 5:
            body = await request.json()
            data = body if isinstance(body, dict) else {}
            try:
                result = await svc.create_promotion(
                    wf_id,
                    data.get("org_id", ""),
                    data.get("from_environment", ""),
                    data.get("to_environment", ""),
                    uid,
                    data.get("approval_id"),
                    data.get("promotion_note", ""),
                )
                return json_resp(result, 201)
            except ValueError as e:
                return error(str(e), 400)

    return error("Not found", 404)


async def handle_webhook_trigger(request, env, path, method, query, ctx):
    """Handle incoming webhook triggers: POST /api/webhooks/workflow/:token"""
    parts = path.rstrip("/").split("/")
    # /api/webhooks/workflow/:token => parts: ["", "api", "webhooks", "workflow", token]
    if len(parts) < 5 or method != "POST":
        return error("Not found", 404)
    token = parts[4]
    svc = WorkflowService(env, ctx)
    try:
        body = await request.json()
        payload = body if isinstance(body, dict) else {}
    except Exception:
        payload = {}
    try:
        result = await svc.handle_webhook_trigger(token, payload)
        return json_resp(result, 201)
    except ValueError as e:
        return error(str(e), 400)
