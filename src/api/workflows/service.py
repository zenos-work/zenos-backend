"""Workflow service — business logic for Steps 20-22."""

import json
import secrets
from typing import Optional
from api.workflows.repository import WorkflowRepository
from utils.helpers import new_id, paginate

VALID_STATUSES = {"draft", "active", "paused", "archived", "error"}
VALID_ENVIRONMENTS = {"dev", "staging", "production"}
VALID_TRIGGER_TYPES = {
    "article_published",
    "article_submitted",
    "lead_captured",
    "form_submitted",
    "webhook",
    "schedule",
    "manual",
    "subflow",
}
VALID_SCOPE_TYPES = {
    "manual",
    "all_author_content",
    "org_wide",
    "tagged_content",
    "team_content",
}
VALID_BIND_TYPES = {
    "all_org_content",
    "by_tag",
    "by_content_type",
    "by_author",
    "by_team",
    "by_security_level",
    "by_premium_status",
    "by_regex_title",
    "manual_selection",
}
VALID_TRIGGER_EVENTS = {
    "on_create",
    "on_submit",
    "on_approve",
    "on_publish",
    "on_update",
    "on_unpublish",
    "on_schedule",
    "on_expire",
}
VALID_TASK_DECISIONS = {"approved", "rejected", "modified"}
VALID_APPROVAL_ACTIONS = {"approved", "rejected", "changes_requested"}
VALID_PERM_TYPES = {"user", "team", "org_role"}
VALID_PERMISSIONS = {"view", "edit", "run", "approve", "manage", "review_tasks"}


class WorkflowService:
    def __init__(self, env, ctx=None):
        self._repo = WorkflowRepository(env.DB, ctx)

    # ═════════════════════════════════════════════════════════
    # Step 20 — Core builder
    # ═════════════════════════════════════════════════════════

    # ── Node types ────────────────────────────────────────────

    async def list_node_types(self, category: Optional[str] = None) -> list:
        if category:
            types = await self._repo.get_node_types_by_category(category)
        else:
            types = await self._repo.get_node_types()
        return [t.to_dict() for t in types]

    # ── Workflows CRUD ────────────────────────────────────────

    async def list_workflows(
        self,
        org_id: str = None,
        owner_id: str = None,
        status: str = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        lim, off = paginate(page, limit)
        if org_id and status:
            items = await self._repo.find_workflows_by_org_status(
                org_id, status, lim, off
            )
        elif org_id:
            items = await self._repo.find_workflows_by_org(org_id, lim, off)
        elif owner_id:
            items = await self._repo.find_workflows_by_owner(owner_id, lim, off)
        else:
            items = []
        total = (
            await self._repo.count_workflows_by_org(org_id)
            if org_id
            else await self._repo.count_workflows_by_owner(owner_id)
            if owner_id
            else 0
        )
        return {
            "workflows": [w.to_dict() for w in items],
            "total": total,
            "page": page,
            "limit": lim,
        }

    async def get_workflow(self, wid: str) -> dict:
        wf = await self._repo.find_workflow(wid)
        if not wf:
            raise ValueError("Workflow not found")
        nodes = await self._repo.get_nodes(wid)
        edges = await self._repo.get_edges(wid)
        d = wf.to_dict(scope="admin")
        d["nodes"] = [n.to_dict() for n in nodes]
        d["edges"] = [e.to_dict() for e in edges]
        return d

    async def create_workflow(
        self,
        org_id: str,
        owner_id: str,
        name: str,
        description: str = "",
        trigger_type: str = "manual",
        environment: str = "dev",
        tags: list = None,
        scope_type: str = "manual",
        scope_filter: dict = None,
        folder_id: str = None,
        approval_required: bool = False,
    ) -> dict:
        if trigger_type not in VALID_TRIGGER_TYPES:
            raise ValueError(f"Invalid trigger_type: {trigger_type}")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {environment}")
        if scope_type not in VALID_SCOPE_TYPES:
            raise ValueError(f"Invalid scope_type: {scope_type}")
        wid = new_id()
        await self._repo.create_workflow(
            wid,
            org_id,
            owner_id,
            name,
            description,
            "draft",
            environment,
            trigger_type,
            json.dumps(tags or []),
            scope_type,
            json.dumps(scope_filter or {}),
            folder_id or None,
            approval_required,
        )
        await self._audit(
            org_id, wid, None, owner_id, "workflow.created", "workflow", wid
        )
        return {"id": wid}

    async def update_workflow(self, wid: str, updated_by: str, **kwargs) -> dict:
        wf = await self._repo.find_workflow(wid)
        if not wf:
            raise ValueError("Workflow not found")
        name = kwargs.get("name", wf.name)
        desc = kwargs.get("description", wf.description)
        status = kwargs.get("status", wf.status)
        env = kwargs.get("environment", wf.environment)
        tt = kwargs.get("trigger_type", wf.trigger_type)
        tags = kwargs.get("tags", wf.tags)
        st = kwargs.get("scope_type", wf.scope_type)
        sf = kwargs.get("scope_filter", wf.scope_filter)
        fid = kwargs.get("folder_id", wf.folder_id)
        ar = kwargs.get("approval_required", wf.approval_required)

        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        if env not in VALID_ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {env}")
        if tt not in VALID_TRIGGER_TYPES:
            raise ValueError(f"Invalid trigger_type: {tt}")

        await self._repo.update_workflow(
            wid,
            name,
            desc,
            status,
            env,
            tt,
            json.dumps(tags) if isinstance(tags, list) else tags,
            st,
            json.dumps(sf) if isinstance(sf, dict) else sf,
            fid or None,
            ar,
        )
        await self._audit(
            wf.org_id, wid, None, updated_by, "workflow.updated", "workflow", wid
        )
        updated = await self._repo.find_workflow(wid)
        return updated.to_dict(scope="admin") if updated else {"id": wid}

    async def delete_workflow(self, wid: str, deleted_by: str) -> None:
        wf = await self._repo.find_workflow(wid)
        if not wf:
            raise ValueError("Workflow not found")
        await self._repo.delete_workflow(wid)
        await self._audit(
            wf.org_id, wid, None, deleted_by, "workflow.deleted", "workflow", wid
        )

    async def clone_workflow(
        self, wid: str, owner_id: str, org_id: str, new_name: str = None
    ) -> dict:
        wf = await self._repo.find_workflow(wid)
        if not wf:
            raise ValueError("Source workflow not found")
        new_id_val = new_id()
        await self._repo.create_workflow(
            new_id_val,
            org_id,
            owner_id,
            new_name or f"{wf.name} (copy)",
            wf.description,
            "draft",
            wf.environment,
            wf.trigger_type,
            json.dumps(wf.tags),
            wf.scope_type,
            json.dumps(wf.scope_filter),
            wf.folder_id or None,
            wf.approval_required,
        )
        # copy nodes
        nodes = await self._repo.get_nodes(wid)
        node_map = {}
        for n in nodes:
            nid = new_id()
            node_map[n.id] = nid
            await self._repo.create_node(
                nid,
                new_id_val,
                n.node_type_id,
                n.label,
                n.position_x,
                n.position_y,
                json.dumps(n.display_config),
                n.connector_binding_id or None,
            )
        # copy edges
        edges = await self._repo.get_edges(wid)
        for e in edges:
            src = node_map.get(e.source_node_id, e.source_node_id)
            tgt = node_map.get(e.target_node_id, e.target_node_id)
            await self._repo.create_edge(
                new_id(), new_id_val, src, tgt, e.condition_label
            )
        await self._audit(
            org_id,
            new_id_val,
            None,
            owner_id,
            "workflow.cloned",
            "workflow",
            new_id_val,
            detail={"cloned_from": wid},
        )
        return {"id": new_id_val, "cloned_from": wid}

    # ── Nodes ─────────────────────────────────────────────────

    async def add_node(
        self,
        workflow_id: str,
        node_type_id: str,
        label: str = "",
        position_x: float = 0,
        position_y: float = 0,
        display_config: dict = None,
        connector_binding_id: str = None,
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        nt = await self._repo.get_node_type(node_type_id)
        if not nt:
            raise ValueError("Invalid node_type_id")
        nid = new_id()
        await self._repo.create_node(
            nid,
            workflow_id,
            node_type_id,
            label,
            position_x,
            position_y,
            json.dumps(display_config or {}),
            connector_binding_id,
        )
        return {"id": nid}

    async def update_node(self, node_id: str, **kwargs) -> dict:
        node = await self._repo.get_node(node_id)
        if not node:
            raise ValueError("Node not found")
        await self._repo.update_node(
            node_id,
            kwargs.get("label", node.label),
            kwargs.get("position_x", node.position_x),
            kwargs.get("position_y", node.position_y),
            json.dumps(kwargs.get("display_config", node.display_config)),
            kwargs.get("connector_binding_id", node.connector_binding_id) or None,
        )
        updated = await self._repo.get_node(node_id)
        return updated.to_dict() if updated else {"id": node_id}

    async def delete_node(self, node_id: str) -> None:
        node = await self._repo.get_node(node_id)
        if not node:
            raise ValueError("Node not found")
        await self._repo.delete_node(node_id)

    # ── Edges ─────────────────────────────────────────────────

    async def add_edge(
        self,
        workflow_id: str,
        source_node_id: str,
        target_node_id: str,
        condition_label: str = "",
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        eid = new_id()
        await self._repo.create_edge(
            eid, workflow_id, source_node_id, target_node_id, condition_label
        )
        return {"id": eid}

    async def delete_edge(self, edge_id: str) -> None:
        edge = await self._repo.get_edge(edge_id)
        if not edge:
            raise ValueError("Edge not found")
        await self._repo.delete_edge(edge_id)

    # ── Versions ──────────────────────────────────────────────

    async def list_versions(self, workflow_id: str) -> list:
        versions = await self._repo.get_versions(workflow_id)
        return [v.to_dict() for v in versions]

    async def create_version(
        self, workflow_id: str, created_by: str, changelog: str = ""
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        latest = await self._repo.get_latest_version(workflow_id)
        ver = (latest.version_number + 1) if latest else 1
        nodes = await self._repo.get_nodes(workflow_id)
        edges = await self._repo.get_edges(workflow_id)
        definition = {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
        }
        vid = new_id()
        await self._repo.create_version(
            vid,
            workflow_id,
            ver,
            json.dumps(definition),
            changelog,
            created_by,
        )
        await self._repo.update_workflow(
            workflow_id,
            wf.name,
            wf.description,
            wf.status,
            wf.environment,
            wf.trigger_type,
            json.dumps(wf.tags),
            wf.scope_type,
            json.dumps(wf.scope_filter),
            wf.folder_id or None,
            wf.approval_required,
        )
        return {"id": vid, "version_number": ver}

    async def restore_version(
        self,
        workflow_id: str,
        restored_by: str,
        version_id: str = "",
        version_number: int = 0,
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")

        version = None
        if version_id:
            version = await self._repo.get_version(version_id)
        elif version_number > 0:
            version = await self._repo.get_version_by_number(
                workflow_id, version_number
            )
        if not version or version.workflow_id != workflow_id:
            raise ValueError("Workflow version not found")

        definition = version.definition or {}
        nodes = definition.get("nodes", []) if isinstance(definition, dict) else []
        edges = definition.get("edges", []) if isinstance(definition, dict) else []

        # Rebuild graph from selected version snapshot.
        existing_edges = await self._repo.get_edges(workflow_id)
        for edge in existing_edges:
            await self._repo.delete_edge(edge.id)

        existing_nodes = await self._repo.get_nodes(workflow_id)
        for node in existing_nodes:
            await self._repo.delete_node(node.id)

        for node in nodes:
            node_data = node if isinstance(node, dict) else {}
            node_id = str(node_data.get("id") or new_id())
            node_type_id = (
                node_data.get("node_type_id")
                or node_data.get("type")
                or (
                    node_data.get("data", {})
                    if isinstance(node_data.get("data"), dict)
                    else {}
                ).get("node_type")
                or "trigger.manual"
            )
            label = (
                node_data.get("label")
                or (
                    node_data.get("data", {})
                    if isinstance(node_data.get("data"), dict)
                    else {}
                ).get("label")
                or ""
            )
            px = node_data.get("position_x")
            py = node_data.get("position_y")
            if px is None or py is None:
                position = (
                    node_data.get("position")
                    if isinstance(node_data.get("position"), dict)
                    else {}
                )
                px = position.get("x", 0)
                py = position.get("y", 0)

            display_config = node_data.get("display_config")
            if not isinstance(display_config, dict):
                display_config = (
                    node_data.get("data")
                    if isinstance(node_data.get("data"), dict)
                    else {}
                )

            await self._repo.create_node(
                node_id,
                workflow_id,
                str(node_type_id),
                str(label),
                float(px or 0),
                float(py or 0),
                json.dumps(display_config),
                node_data.get("connector_binding_id"),
            )

        for edge in edges:
            edge_data = edge if isinstance(edge, dict) else {}
            source = edge_data.get("source_node_id") or edge_data.get("source")
            target = edge_data.get("target_node_id") or edge_data.get("target")
            if not source or not target:
                continue
            await self._repo.create_edge(
                str(edge_data.get("id") or new_id()),
                workflow_id,
                str(source),
                str(target),
                str(edge_data.get("condition_label") or edge_data.get("label") or ""),
            )

        await self._repo.update_workflow_definition_version(
            workflow_id, version.version_number
        )
        await self._audit(
            wf.org_id,
            workflow_id,
            None,
            restored_by,
            "workflow.version_restored",
            "workflow_version",
            version.id,
            detail={"version_number": version.version_number},
        )
        return {"workflow_id": workflow_id, "restored_version": version.version_number}

    # ── Webhooks ──────────────────────────────────────────────

    async def create_webhook(
        self, workflow_id: str, node_id: str = None, method: str = "POST"
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        wid = new_id()
        token = secrets.token_urlsafe(32)
        await self._repo.create_webhook(wid, workflow_id, node_id, token, method)
        return {"id": wid, "token": token}

    async def list_webhooks(self, workflow_id: str) -> list:
        hooks = await self._repo.get_webhooks(workflow_id)
        return [h.to_dict() for h in hooks]

    async def delete_webhook(self, webhook_id: str) -> None:
        wh = await self._repo.get_webhook(webhook_id)
        if not wh:
            raise ValueError("Webhook not found")
        await self._repo.delete_webhook(webhook_id)

    # ── Templates ─────────────────────────────────────────────

    async def list_templates(
        self, category: str = None, page: int = 1, limit: int = 20
    ) -> dict:
        lim, off = paginate(page, limit)
        if category:
            items = await self._repo.get_templates_by_category(category, lim, off)
        else:
            items = await self._repo.get_templates(lim, off)
        return {"templates": [t.to_dict() for t in items], "page": page, "limit": lim}

    async def publish_template(
        self,
        workflow_id: str,
        title: str,
        short_desc: str,
        category: str,
        use_case_tags: list = None,
        preview_image: str = None,
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        tid = new_id()
        await self._repo.create_template(
            tid,
            workflow_id,
            title,
            short_desc,
            category,
            json.dumps(use_case_tags or []),
            preview_image or "",
        )
        return {"id": tid}

    async def clone_from_template(
        self, template_id: str, org_id: str, owner_id: str
    ) -> dict:
        tpl = await self._repo.get_template(template_id)
        if not tpl:
            raise ValueError("Template not found")
        await self._repo.increment_template_download(template_id)
        return await self.clone_workflow(tpl.workflow_id, owner_id, org_id)

    # ── Integrations ──────────────────────────────────────────

    async def list_integrations(self, org_id: str) -> list:
        items = await self._repo.get_integrations(org_id)
        return [i.to_dict() for i in items]

    async def create_integration(
        self,
        org_id: str,
        integration_type: str,
        name: str,
        kv_secret_key: str,
        created_by: str,
    ) -> dict:
        iid = new_id()
        await self._repo.create_integration(
            iid, org_id, integration_type, name, kv_secret_key, created_by
        )
        return {"id": iid}

    async def delete_integration(self, integration_id: str) -> None:
        integ = await self._repo.get_integration(integration_id)
        if not integ:
            raise ValueError("Integration not found")
        await self._repo.delete_integration(integration_id)

    # ═════════════════════════════════════════════════════════
    # Step 21 — Execution engine
    # ═════════════════════════════════════════════════════════

    async def trigger_run(
        self,
        workflow_id: str,
        triggered_by: str = "manual",
        trigger_payload: dict = None,
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        if wf.status != "active":
            raise ValueError("Workflow must be active to run")
        nodes = await self._repo.get_nodes(workflow_id)
        rid = new_id()
        await self._repo.create_run(
            rid,
            workflow_id,
            triggered_by,
            json.dumps(trigger_payload or {}),
            len(nodes),
        )
        # Create pending steps for each node
        for n in nodes:
            sid = new_id()
            await self._repo.create_run_step(
                sid,
                rid,
                n.id,
                n.node_type_id,
                1,
                json.dumps(trigger_payload or {}),
            )
        await self._audit(
            wf.org_id,
            workflow_id,
            rid,
            None,
            "run.started",
            "workflow_run",
            rid,
            detail={"triggered_by": triggered_by},
        )
        return {
            "id": rid,
            "workflow_id": workflow_id,
            "status": "running",
            "steps_total": len(nodes),
        }

    async def handle_webhook_trigger(self, token: str, payload: dict) -> dict:
        wh = await self._repo.get_webhook_by_token(token)
        if not wh:
            raise ValueError("Invalid webhook token")
        await self._repo.record_webhook_hit(wh.id)
        return await self.trigger_run(wh.workflow_id, "webhook", payload)

    async def list_runs(self, workflow_id: str, page: int = 1, limit: int = 20) -> dict:
        lim, off = paginate(page, limit)
        runs = await self._repo.get_runs(workflow_id, lim, off)
        total = await self._repo.count_runs(workflow_id)
        return {
            "runs": [r.to_dict() for r in runs],
            "total": total,
            "page": page,
            "limit": lim,
        }

    async def get_run(self, run_id: str) -> dict:
        run = await self._repo.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        steps = await self._repo.get_run_steps(run_id)
        d = run.to_dict(scope="admin")
        d["steps"] = [s.to_dict() for s in steps]
        return d

    async def cancel_run(self, run_id: str) -> dict:
        run = await self._repo.get_run(run_id)
        if not run:
            raise ValueError("Run not found")
        if run.status != "running":
            raise ValueError("Only running workflows can be cancelled")
        await self._repo.cancel_run(run_id)
        await self._repo.update_run_stats(run.workflow_id, "cancelled")
        return {"id": run_id, "status": "cancelled"}

    # ═════════════════════════════════════════════════════════
    # Step 22 — HITL + Enterprise
    # ═════════════════════════════════════════════════════════

    # ── Human tasks ───────────────────────────────────────────

    async def list_tasks(
        self, user_id: str = None, org_id: str = None, page: int = 1, limit: int = 20
    ) -> dict:
        lim, off = paginate(page, limit)
        if user_id:
            tasks = await self._repo.get_tasks_for_user(user_id, lim, off)
        elif org_id:
            tasks = await self._repo.get_tasks_for_org(org_id, lim, off)
        else:
            tasks = []
        return {"tasks": [t.to_dict() for t in tasks], "page": page, "limit": lim}

    async def get_task(self, task_id: str) -> dict:
        task = await self._repo.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        return task.to_dict(scope="admin")

    async def start_task_review(self, task_id: str, reviewer_id: str) -> dict:
        task = await self._repo.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.status != "pending":
            raise ValueError("Task is not pending")
        await self._repo.start_task_review(task_id, reviewer_id)
        updated = await self._repo.get_task(task_id)
        return updated.to_dict(scope="admin") if updated else {"id": task_id}

    async def complete_task(
        self,
        task_id: str,
        reviewer_id: str,
        decision: str,
        reviewer_note: str = "",
        output_data: dict = None,
    ) -> dict:
        task = await self._repo.get_task(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.status not in ("pending", "in_review"):
            raise ValueError("Task cannot be completed in current status")
        if decision not in VALID_TASK_DECISIONS:
            raise ValueError(f"Invalid decision: {decision}")
        status = "completed" if decision in ("approved", "modified") else "rejected"
        await self._repo.complete_task(
            task_id,
            status,
            decision,
            reviewer_id,
            reviewer_note,
            json.dumps(output_data or {}),
        )
        await self._audit(
            task.org_id,
            task.workflow_id,
            task.run_id,
            reviewer_id,
            "task.completed",
            "human_task",
            task_id,
            detail={"decision": decision},
        )
        return {"id": task_id, "status": status, "decision": decision}

    # ── Approvals ─────────────────────────────────────────────

    async def request_approval(
        self,
        workflow_id: str,
        requested_by: str,
        assigned_to: str = None,
        request_note: str = "",
        expires_at: str = None,
    ) -> dict:
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        latest = await self._repo.get_latest_version(workflow_id)
        ver = latest.version_number if latest else wf.definition_version
        aid = new_id()
        await self._repo.create_approval(
            aid,
            workflow_id,
            ver,
            requested_by,
            assigned_to,
            request_note,
            expires_at,
        )
        await self._repo.update_workflow_status(workflow_id, "draft")
        await self._audit(
            wf.org_id,
            workflow_id,
            None,
            requested_by,
            "approval.requested",
            "workflow_approval",
            aid,
        )
        return {"id": aid, "version_number": ver}

    async def review_approval(
        self, approval_id: str, reviewed_by: str, action: str, review_note: str = ""
    ) -> dict:
        appr = await self._repo.get_approval(approval_id)
        if not appr:
            raise ValueError("Approval not found")
        if appr.status != "pending":
            raise ValueError("Approval is not pending")
        if action not in VALID_APPROVAL_ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        await self._repo.review_approval(approval_id, action, review_note, reviewed_by)
        if action == "approved":
            wf = await self._repo.find_workflow(appr.workflow_id)
            if wf:
                await self._repo.update_workflow_status(appr.workflow_id, "active")
        return {"id": approval_id, "status": action}

    async def list_approvals(self, workflow_id: str) -> list:
        items = await self._repo.get_approvals(workflow_id)
        return [a.to_dict() for a in items]

    async def list_pending_approvals(self, user_id: str) -> list:
        items = await self._repo.get_pending_approvals_for_user(user_id)
        return [a.to_dict() for a in items]

    # ── Content bindings ──────────────────────────────────────

    async def list_bindings(self, workflow_id: str) -> list:
        items = await self._repo.get_bindings_by_workflow(workflow_id)
        return [b.to_dict() for b in items]

    async def create_binding(
        self,
        workflow_id: str,
        org_id: str,
        bind_type: str,
        bind_criteria: dict = None,
        trigger_event: str = "on_submit",
        priority: int = 100,
        created_by: str = "",
    ) -> dict:
        if bind_type not in VALID_BIND_TYPES:
            raise ValueError(f"Invalid bind_type: {bind_type}")
        if trigger_event not in VALID_TRIGGER_EVENTS:
            raise ValueError(f"Invalid trigger_event: {trigger_event}")
        bid = new_id()
        await self._repo.create_binding(
            bid,
            workflow_id,
            org_id,
            bind_type,
            json.dumps(bind_criteria or {}),
            trigger_event,
            priority,
            created_by,
        )
        return {"id": bid}

    async def update_binding(self, binding_id: str, **kwargs) -> dict:
        bind = await self._repo.get_binding(binding_id)
        if not bind:
            raise ValueError("Binding not found")
        bt = kwargs.get("bind_type", bind.bind_type)
        te = kwargs.get("trigger_event", bind.trigger_event)
        if bt not in VALID_BIND_TYPES:
            raise ValueError(f"Invalid bind_type: {bt}")
        if te not in VALID_TRIGGER_EVENTS:
            raise ValueError(f"Invalid trigger_event: {te}")
        await self._repo.update_binding(
            binding_id,
            bt,
            json.dumps(kwargs.get("bind_criteria", bind.bind_criteria)),
            te,
            kwargs.get("priority", bind.priority),
            kwargs.get("is_active", bind.is_active),
        )
        return {"id": binding_id}

    async def delete_binding(self, binding_id: str) -> None:
        bind = await self._repo.get_binding(binding_id)
        if not bind:
            raise ValueError("Binding not found")
        await self._repo.delete_binding(binding_id)

    # ── Permissions ───────────────────────────────────────────

    async def list_permissions(self, workflow_id: str) -> list:
        items = await self._repo.get_permissions(workflow_id)
        return [p.to_dict() for p in items]

    async def grant_permission(
        self,
        workflow_id: str,
        grantee_type: str,
        grantee_id: str,
        permission: str,
        granted_by: str,
    ) -> dict:
        if grantee_type not in VALID_PERM_TYPES:
            raise ValueError(f"Invalid grantee_type: {grantee_type}")
        if permission not in VALID_PERMISSIONS:
            raise ValueError(f"Invalid permission: {permission}")
        pid = new_id()
        await self._repo.create_permission(
            pid,
            workflow_id,
            grantee_type,
            grantee_id,
            permission,
            granted_by,
        )
        return {"id": pid}

    async def revoke_permission(self, permission_id: str) -> None:
        await self._repo.delete_permission(permission_id)

    # ── Run messages ──────────────────────────────────────────

    async def list_messages(self, run_id: str) -> list:
        items = await self._repo.get_messages(run_id)
        return [m.to_dict() for m in items]

    async def add_message(
        self,
        run_id: str,
        workflow_id: str,
        sender_id: str,
        content: str,
        sender_role: str = "author",
        message_type: str = "comment",
        step_id: str = None,
        task_id: str = None,
        attachment_url: str = None,
        attachment_type: str = None,
        is_internal: bool = False,
    ) -> dict:
        mid = new_id()
        await self._repo.create_message(
            mid,
            run_id,
            workflow_id,
            step_id,
            task_id,
            sender_id,
            sender_role,
            content,
            message_type,
            attachment_url or "",
            attachment_type or "",
            is_internal,
        )
        return {"id": mid}

    # ── Policies ──────────────────────────────────────────────

    async def list_policies(self, org_id: str) -> list:
        items = await self._repo.get_policies(org_id)
        return [p.to_dict() for p in items]

    async def create_policy(
        self,
        org_id: str,
        policy_type: str,
        policy_value: dict,
        enforced_by: str = "system",
        created_by: str = "",
    ) -> dict:
        pid = new_id()
        await self._repo.create_policy(
            pid,
            org_id,
            policy_type,
            json.dumps(policy_value),
            enforced_by,
            created_by,
        )
        return {"id": pid}

    async def update_policy(
        self, policy_id: str, policy_value: dict = None, is_active: bool = None
    ) -> dict:
        pol = await self._repo.get_policy(policy_id)
        if not pol:
            raise ValueError("Policy not found")
        await self._repo.update_policy(
            policy_id,
            json.dumps(policy_value)
            if policy_value is not None
            else json.dumps(pol.policy_value),
            is_active if is_active is not None else pol.is_active,
        )
        return {"id": policy_id}

    # ── Folders ───────────────────────────────────────────────

    async def list_folders(self, org_id: str) -> list:
        items = await self._repo.get_folders(org_id)
        return [f.to_dict() for f in items]

    async def create_folder(
        self,
        org_id: str,
        name: str,
        parent_id: str = None,
        description: str = "",
        icon: str = "",
        sort_order: int = 0,
        created_by: str = "",
    ) -> dict:
        fid = new_id()
        await self._repo.create_folder(
            fid,
            org_id,
            parent_id,
            name,
            description,
            icon,
            sort_order,
            created_by,
        )
        return {"id": fid}

    async def update_folder(self, folder_id: str, **kwargs) -> dict:
        folder = await self._repo.get_folder(folder_id)
        if not folder:
            raise ValueError("Folder not found")
        await self._repo.update_folder(
            folder_id,
            kwargs.get("name", folder.name),
            kwargs.get("description", folder.description),
            kwargs.get("icon", folder.icon),
            kwargs.get("sort_order", folder.sort_order),
            kwargs.get("parent_id", folder.parent_id) or None,
        )
        return {"id": folder_id}

    async def delete_folder(self, folder_id: str) -> None:
        folder = await self._repo.get_folder(folder_id)
        if not folder:
            raise ValueError("Folder not found")
        await self._repo.delete_folder(folder_id)

    # ── Schedules ─────────────────────────────────────────────

    async def list_schedules(self, workflow_id: str = None, org_id: str = None) -> list:
        if workflow_id:
            items = await self._repo.get_schedules_by_workflow(workflow_id)
        elif org_id:
            items = await self._repo.get_schedules_by_org(org_id)
        else:
            items = []
        return [s.to_dict() for s in items]

    async def create_schedule(
        self,
        org_id: str,
        workflow_id: str,
        name: str,
        cron_expression: str,
        timezone: str = "UTC",
        next_fire_at: str = None,
        created_by: str = "",
    ) -> dict:
        sid = new_id()
        await self._repo.create_schedule(
            sid,
            org_id,
            workflow_id,
            name,
            cron_expression,
            timezone,
            next_fire_at,
            created_by,
        )
        return {"id": sid}

    async def update_schedule(self, schedule_id: str, **kwargs) -> dict:
        sched = await self._repo.get_schedule(schedule_id)
        if not sched:
            raise ValueError("Schedule not found")
        await self._repo.update_schedule(
            schedule_id,
            kwargs.get("name", sched.name),
            kwargs.get("cron_expression", sched.cron_expression),
            kwargs.get("timezone", sched.timezone),
            kwargs.get("is_active", sched.is_active),
            kwargs.get("next_fire_at", sched.next_fire_at),
        )
        return {"id": schedule_id}

    async def delete_schedule(self, schedule_id: str) -> None:
        sched = await self._repo.get_schedule(schedule_id)
        if not sched:
            raise ValueError("Schedule not found")
        await self._repo.delete_schedule(schedule_id)

    # ── Audit log ─────────────────────────────────────────────

    async def get_audit_log(
        self,
        workflow_id: str = None,
        org_id: str = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        lim, off = paginate(page, limit)
        if workflow_id:
            items = await self._repo.get_audit_by_workflow(workflow_id, lim, off)
        elif org_id:
            items = await self._repo.get_audit_by_org(org_id, lim, off)
        else:
            items = []
        return {"audit_log": [a.to_dict() for a in items], "page": page, "limit": lim}

    # ── Costs ─────────────────────────────────────────────────

    async def get_run_costs(self, run_id: str) -> list:
        items = await self._repo.get_costs_by_run(run_id)
        return [c.to_dict() for c in items]

    async def get_cost_summary(self, workflow_id: str) -> dict:
        summary = await self._repo.get_cost_summary(workflow_id)
        return summary or {}

    # ── Promotions ────────────────────────────────────────────

    async def list_promotions(self, workflow_id: str) -> list:
        items = await self._repo.get_promotions(workflow_id)
        return [p.to_dict() for p in items]

    async def create_promotion(
        self,
        workflow_id: str,
        org_id: str,
        from_env: str,
        to_env: str,
        promoted_by: str,
        approval_id: str = None,
        promotion_note: str = "",
    ) -> dict:
        if from_env not in VALID_ENVIRONMENTS or to_env not in VALID_ENVIRONMENTS:
            raise ValueError("Invalid environment")
        wf = await self._repo.find_workflow(workflow_id)
        if not wf:
            raise ValueError("Workflow not found")
        latest = await self._repo.get_latest_version(workflow_id)
        ver = latest.version_number if latest else wf.definition_version
        pid = new_id()
        await self._repo.create_promotion(
            pid,
            workflow_id,
            org_id,
            from_env,
            to_env,
            ver,
            promoted_by,
            approval_id,
            promotion_note,
        )
        return {"id": pid, "version_number": ver}

    # ── Internal helper ───────────────────────────────────────

    async def _audit(
        self,
        org_id,
        workflow_id,
        run_id,
        actor_id,
        action,
        resource_type="",
        resource_id="",
        detail=None,
        ip_hash="",
    ):
        try:
            await self._repo.log_audit(
                new_id(),
                org_id or "",
                workflow_id or "",
                run_id or "",
                actor_id or "",
                action,
                resource_type,
                resource_id,
                json.dumps(detail or {}),
                ip_hash,
            )
        except Exception:
            pass  # audit failures should not break main flow
