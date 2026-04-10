"""Repository for all workflow tables (Steps 20-22)."""

from db.repository import BaseRepository
from api.workflows import queries as Q
from models.workflow.model import (
    Workflow,
    WorkflowNode,
    WorkflowEdge,
    WorkflowVersion,
    WorkflowNodeType,
    WorkflowWebhook,
    WorkflowIntegration,
    WorkflowTemplateListing,
    WorkflowRun,
    WorkflowRunStep,
    WorkflowApproval,
    WorkflowHumanTask,
    WorkflowContentBinding,
    WorkflowPermission,
    WorkflowRunMessage,
    WorkflowPolicy,
    WorkflowFolder,
    WorkflowSchedule,
    WorkflowAuditLog,
    WorkflowRunCost,
    WorkflowPromotion,
)


class WorkflowRepository(BaseRepository):
    """Aggregates all workflow-related data access."""

    def __init__(self, db, ctx=None):
        super().__init__(db, ctx)

    # ── helpers ───────────────────────────────────────────────
    async def _one(self, Model, sql, params=None):
        return await self.map_one(sql, params or [], Model.from_row)

    async def _many(self, Model, sql, params=None):
        return await self.map_many(sql, params or [], Model.from_row)

    # ═════════════════════════════════════════════════════════
    # Step 20 — Core builder
    # ═════════════════════════════════════════════════════════

    # ── Node types ────────────────────────────────────────────
    async def get_node_types(self):
        return await self._many(WorkflowNodeType, Q.GET_NODE_TYPES)

    async def get_node_types_by_category(self, category):
        return await self._many(
            WorkflowNodeType, Q.GET_NODE_TYPES_BY_CATEGORY, [category]
        )

    async def get_node_type(self, nid):
        return await self._one(WorkflowNodeType, Q.GET_NODE_TYPE_BY_ID, [nid])

    # ── Workflows ─────────────────────────────────────────────
    async def find_workflows_by_org(self, org_id, limit, offset):
        return await self._many(
            Workflow, Q.GET_WORKFLOWS_BY_ORG, [org_id, limit, offset]
        )

    async def find_workflows_by_owner(self, owner_id, limit, offset):
        return await self._many(
            Workflow, Q.GET_WORKFLOWS_BY_OWNER, [owner_id, limit, offset]
        )

    async def find_workflows_by_org_status(self, org_id, status, limit, offset):
        return await self._many(
            Workflow, Q.GET_WORKFLOWS_BY_ORG_AND_STATUS, [org_id, status, limit, offset]
        )

    async def find_workflow(self, wid):
        return await self._one(Workflow, Q.GET_WORKFLOW_BY_ID, [wid])

    async def count_workflows_by_org(self, org_id):
        row = await self.find_one(Q.COUNT_WORKFLOWS_BY_ORG, [org_id])
        return row["cnt"] if row else 0

    async def count_workflows_by_owner(self, owner_id):
        row = await self.find_one(Q.COUNT_WORKFLOWS_BY_OWNER, [owner_id])
        return row["cnt"] if row else 0

    async def create_workflow(
        self,
        wid,
        org_id,
        owner_id,
        name,
        desc,
        status,
        env,
        trigger_type,
        tags,
        scope_type,
        scope_filter,
        folder_id,
        approval_required,
    ):
        await self.execute(
            Q.INSERT_WORKFLOW,
            [
                wid,
                org_id,
                owner_id,
                name,
                desc,
                status,
                env,
                trigger_type,
                tags,
                scope_type,
                scope_filter,
                folder_id,
                1 if approval_required else 0,
            ],
        )

    async def update_workflow(
        self,
        wid,
        name,
        desc,
        status,
        env,
        trigger_type,
        tags,
        scope_type,
        scope_filter,
        folder_id,
        approval_required,
    ):
        await self.execute(
            Q.UPDATE_WORKFLOW,
            [
                name,
                desc,
                status,
                env,
                trigger_type,
                tags,
                scope_type,
                scope_filter,
                folder_id,
                1 if approval_required else 0,
                wid,
            ],
        )

    async def delete_workflow(self, wid):
        await self.execute(Q.DELETE_WORKFLOW, [wid])

    async def update_workflow_status(self, wid, status):
        await self.execute(Q.UPDATE_WORKFLOW_STATUS, [status, wid])

    async def update_run_stats(self, wid, status):
        await self.execute(Q.UPDATE_WORKFLOW_RUN_STATS, [status, status, status, wid])

    # ── Nodes ─────────────────────────────────────────────────
    async def get_nodes(self, workflow_id):
        return await self._many(WorkflowNode, Q.GET_NODES_BY_WORKFLOW, [workflow_id])

    async def get_node(self, nid):
        return await self._one(WorkflowNode, Q.GET_NODE_BY_ID, [nid])

    async def create_node(
        self,
        nid,
        workflow_id,
        node_type_id,
        label,
        px,
        py,
        display_config,
        connector_binding_id,
    ):
        await self.execute(
            Q.INSERT_NODE,
            [
                nid,
                workflow_id,
                node_type_id,
                label,
                px,
                py,
                display_config,
                connector_binding_id,
            ],
        )

    async def update_node(
        self, nid, label, px, py, display_config, connector_binding_id
    ):
        await self.execute(
            Q.UPDATE_NODE, [label, px, py, display_config, connector_binding_id, nid]
        )

    async def delete_node(self, nid):
        await self.execute(Q.DELETE_NODE, [nid])

    # ── Edges ─────────────────────────────────────────────────
    async def get_edges(self, workflow_id):
        return await self._many(WorkflowEdge, Q.GET_EDGES_BY_WORKFLOW, [workflow_id])

    async def get_edge(self, eid):
        return await self._one(WorkflowEdge, Q.GET_EDGE_BY_ID, [eid])

    async def create_edge(self, eid, workflow_id, src, tgt, condition_label):
        await self.execute(Q.INSERT_EDGE, [eid, workflow_id, src, tgt, condition_label])

    async def delete_edge(self, eid):
        await self.execute(Q.DELETE_EDGE, [eid])

    # ── Versions ──────────────────────────────────────────────
    async def get_versions(self, workflow_id):
        return await self._many(
            WorkflowVersion, Q.GET_VERSIONS_BY_WORKFLOW, [workflow_id]
        )

    async def get_version(self, vid):
        return await self._one(WorkflowVersion, Q.GET_VERSION_BY_ID, [vid])

    async def get_latest_version(self, workflow_id):
        return await self._one(WorkflowVersion, Q.GET_LATEST_VERSION, [workflow_id])

    async def create_version(
        self, vid, workflow_id, version_number, definition, changelog, created_by
    ):
        await self.execute(
            Q.INSERT_VERSION,
            [
                vid,
                workflow_id,
                version_number,
                definition,
                changelog,
                created_by,
            ],
        )

    # ── Webhooks ──────────────────────────────────────────────
    async def get_webhooks(self, workflow_id):
        return await self._many(
            WorkflowWebhook, Q.GET_WEBHOOKS_BY_WORKFLOW, [workflow_id]
        )

    async def get_webhook_by_token(self, token):
        return await self._one(WorkflowWebhook, Q.GET_WEBHOOK_BY_TOKEN, [token])

    async def get_webhook(self, wid):
        return await self._one(WorkflowWebhook, Q.GET_WEBHOOK_BY_ID, [wid])

    async def create_webhook(self, wid, workflow_id, node_id, token, method):
        await self.execute(Q.INSERT_WEBHOOK, [wid, workflow_id, node_id, token, method])

    async def record_webhook_hit(self, wid):
        await self.execute(Q.UPDATE_WEBHOOK_HIT, [wid])

    async def delete_webhook(self, wid):
        await self.execute(Q.DELETE_WEBHOOK, [wid])

    # ── Templates ─────────────────────────────────────────────
    async def get_templates(self, limit, offset):
        return await self._many(
            WorkflowTemplateListing, Q.GET_TEMPLATES, [limit, offset]
        )

    async def get_templates_by_category(self, category, limit, offset):
        return await self._many(
            WorkflowTemplateListing,
            Q.GET_TEMPLATES_BY_CATEGORY,
            [category, limit, offset],
        )

    async def get_template(self, tid):
        return await self._one(WorkflowTemplateListing, Q.GET_TEMPLATE_BY_ID, [tid])

    async def create_template(
        self,
        tid,
        workflow_id,
        title,
        short_desc,
        category,
        use_case_tags,
        preview_image,
    ):
        await self.execute(
            Q.INSERT_TEMPLATE,
            [
                tid,
                workflow_id,
                title,
                short_desc,
                category,
                use_case_tags,
                preview_image,
            ],
        )

    async def increment_template_download(self, tid):
        await self.execute(Q.UPDATE_TEMPLATE_DOWNLOAD, [tid])

    # ── Integrations ──────────────────────────────────────────
    async def get_integrations(self, org_id):
        return await self._many(
            WorkflowIntegration, Q.GET_INTEGRATIONS_BY_ORG, [org_id]
        )

    async def get_integration(self, iid):
        return await self._one(WorkflowIntegration, Q.GET_INTEGRATION_BY_ID, [iid])

    async def create_integration(self, iid, org_id, itype, name, kv_key, created_by):
        await self.execute(
            Q.INSERT_INTEGRATION, [iid, org_id, itype, name, kv_key, created_by]
        )

    async def delete_integration(self, iid):
        await self.execute(Q.DELETE_INTEGRATION, [iid])

    # ═════════════════════════════════════════════════════════
    # Step 21 — Execution engine
    # ═════════════════════════════════════════════════════════

    async def get_runs(self, workflow_id, limit, offset):
        return await self._many(
            WorkflowRun, Q.GET_RUNS_BY_WORKFLOW, [workflow_id, limit, offset]
        )

    async def get_run(self, rid):
        return await self._one(WorkflowRun, Q.GET_RUN_BY_ID, [rid])

    async def count_runs(self, workflow_id):
        row = await self.find_one(Q.COUNT_RUNS_BY_WORKFLOW, [workflow_id])
        return row["cnt"] if row else 0

    async def create_run(
        self, rid, workflow_id, triggered_by, trigger_payload, steps_total
    ):
        await self.execute(
            Q.INSERT_RUN, [rid, workflow_id, triggered_by, trigger_payload, steps_total]
        )

    async def finish_run(
        self,
        rid,
        status,
        duration_ms,
        error_message,
        steps_succeeded,
        steps_failed,
        final_context,
    ):
        await self.execute(
            Q.UPDATE_RUN_STATUS,
            [
                status,
                duration_ms,
                error_message,
                steps_succeeded,
                steps_failed,
                final_context,
                rid,
            ],
        )

    async def cancel_run(self, rid):
        await self.execute(Q.CANCEL_RUN, [rid])

    async def set_run_waiting(self, rid, task_id):
        await self.execute(Q.SET_RUN_WAITING, [task_id, rid])

    async def get_run_steps(self, run_id):
        return await self._many(WorkflowRunStep, Q.GET_RUN_STEPS, [run_id])

    async def get_run_step(self, sid):
        return await self._one(WorkflowRunStep, Q.GET_RUN_STEP_BY_ID, [sid])

    async def create_run_step(
        self, sid, run_id, node_id, node_type_id, attempt, input_data
    ):
        await self.execute(
            Q.INSERT_RUN_STEP, [sid, run_id, node_id, node_type_id, attempt, input_data]
        )

    async def update_run_step(
        self, sid, status, output_data, error_message, duration_ms
    ):
        await self.execute(
            Q.UPDATE_RUN_STEP,
            [status, output_data, error_message, status, duration_ms, sid],
        )

    # ═════════════════════════════════════════════════════════
    # Step 22 — HITL + Enterprise
    # ═════════════════════════════════════════════════════════

    # ── Human tasks ───────────────────────────────────────────
    async def get_tasks_for_user(self, user_id, limit, offset):
        return await self._many(
            WorkflowHumanTask, Q.GET_TASKS_BY_USER, [user_id, user_id, limit, offset]
        )

    async def get_tasks_for_org(self, org_id, limit, offset):
        return await self._many(
            WorkflowHumanTask, Q.GET_TASKS_BY_ORG, [org_id, limit, offset]
        )

    async def get_task(self, tid):
        return await self._one(WorkflowHumanTask, Q.GET_TASK_BY_ID, [tid])

    async def create_task(
        self,
        tid,
        run_id,
        step_id,
        workflow_id,
        org_id,
        assigned_to,
        assigned_role,
        assigned_team_id,
        task_title,
        instruction_text,
        input_data,
        editable_data,
        context_snapshot,
        priority,
        deadline_at,
    ):
        await self.execute(
            Q.INSERT_TASK,
            [
                tid,
                run_id,
                step_id,
                workflow_id,
                org_id,
                assigned_to,
                assigned_role,
                assigned_team_id,
                task_title,
                instruction_text,
                input_data,
                editable_data,
                context_snapshot,
                priority,
                deadline_at,
            ],
        )

    async def complete_task(
        self, tid, status, decision, reviewer_id, reviewer_note, output_data
    ):
        await self.execute(
            Q.UPDATE_TASK_DECISION,
            [
                status,
                decision,
                reviewer_id,
                reviewer_note,
                output_data,
                tid,
            ],
        )

    async def start_task_review(self, tid, reviewer_id):
        await self.execute(Q.UPDATE_TASK_START_REVIEW, [reviewer_id, tid])

    # ── Approvals ─────────────────────────────────────────────
    async def get_approvals(self, workflow_id):
        return await self._many(
            WorkflowApproval, Q.GET_APPROVALS_BY_WORKFLOW, [workflow_id]
        )

    async def get_approval(self, aid):
        return await self._one(WorkflowApproval, Q.GET_APPROVAL_BY_ID, [aid])

    async def get_pending_approvals_for_user(self, user_id):
        return await self._many(
            WorkflowApproval, Q.GET_PENDING_APPROVALS_FOR_USER, [user_id]
        )

    async def create_approval(
        self,
        aid,
        workflow_id,
        version_number,
        requested_by,
        assigned_to,
        request_note,
        expires_at,
    ):
        await self.execute(
            Q.INSERT_APPROVAL,
            [
                aid,
                workflow_id,
                version_number,
                requested_by,
                assigned_to,
                request_note,
                expires_at,
            ],
        )

    async def review_approval(self, aid, status, review_note, reviewed_by):
        await self.execute(Q.UPDATE_APPROVAL, [status, review_note, reviewed_by, aid])

    # ── Content bindings ──────────────────────────────────────
    async def get_bindings_by_workflow(self, workflow_id):
        return await self._many(
            WorkflowContentBinding, Q.GET_BINDINGS_BY_WORKFLOW, [workflow_id]
        )

    async def get_bindings_by_org(self, org_id):
        return await self._many(WorkflowContentBinding, Q.GET_BINDINGS_BY_ORG, [org_id])

    async def get_binding(self, bid):
        return await self._one(WorkflowContentBinding, Q.GET_BINDING_BY_ID, [bid])

    async def create_binding(
        self,
        bid,
        workflow_id,
        org_id,
        bind_type,
        bind_criteria,
        trigger_event,
        priority,
        created_by,
    ):
        await self.execute(
            Q.INSERT_BINDING,
            [
                bid,
                workflow_id,
                org_id,
                bind_type,
                bind_criteria,
                trigger_event,
                priority,
                created_by,
            ],
        )

    async def update_binding(
        self, bid, bind_type, bind_criteria, trigger_event, priority, is_active
    ):
        await self.execute(
            Q.UPDATE_BINDING,
            [
                bind_type,
                bind_criteria,
                trigger_event,
                priority,
                1 if is_active else 0,
                bid,
            ],
        )

    async def delete_binding(self, bid):
        await self.execute(Q.DELETE_BINDING, [bid])

    # ── Permissions ───────────────────────────────────────────
    async def get_permissions(self, workflow_id):
        return await self._many(
            WorkflowPermission, Q.GET_PERMISSIONS_BY_WORKFLOW, [workflow_id]
        )

    async def get_permissions_for_user(self, workflow_id, user_id, user_role):
        return await self._many(
            WorkflowPermission,
            Q.GET_PERMISSIONS_FOR_USER,
            [workflow_id, user_id, user_role],
        )

    async def create_permission(
        self, pid, workflow_id, grantee_type, grantee_id, permission, granted_by
    ):
        await self.execute(
            Q.INSERT_PERMISSION,
            [
                pid,
                workflow_id,
                grantee_type,
                grantee_id,
                permission,
                granted_by,
            ],
        )

    async def delete_permission(self, pid):
        await self.execute(Q.DELETE_PERMISSION, [pid])

    # ── Run messages ──────────────────────────────────────────
    async def get_messages(self, run_id):
        return await self._many(WorkflowRunMessage, Q.GET_MESSAGES_BY_RUN, [run_id])

    async def create_message(
        self,
        mid,
        run_id,
        workflow_id,
        step_id,
        task_id,
        sender_id,
        sender_role,
        content,
        message_type,
        attachment_url,
        attachment_type,
        is_internal,
    ):
        await self.execute(
            Q.INSERT_MESSAGE,
            [
                mid,
                run_id,
                workflow_id,
                step_id,
                task_id,
                sender_id,
                sender_role,
                content,
                message_type,
                attachment_url,
                attachment_type,
                1 if is_internal else 0,
            ],
        )

    # ── Policies ──────────────────────────────────────────────
    async def get_policies(self, org_id):
        return await self._many(WorkflowPolicy, Q.GET_POLICIES_BY_ORG, [org_id])

    async def get_policy(self, pid):
        return await self._one(WorkflowPolicy, Q.GET_POLICY_BY_ID, [pid])

    async def create_policy(
        self, pid, org_id, policy_type, policy_value, enforced_by, created_by
    ):
        await self.execute(
            Q.INSERT_POLICY,
            [
                pid,
                org_id,
                policy_type,
                policy_value,
                enforced_by,
                created_by,
            ],
        )

    async def update_policy(self, pid, policy_value, is_active):
        await self.execute(Q.UPDATE_POLICY, [policy_value, 1 if is_active else 0, pid])

    # ── Folders ───────────────────────────────────────────────
    async def get_folders(self, org_id):
        return await self._many(WorkflowFolder, Q.GET_FOLDERS_BY_ORG, [org_id])

    async def get_folder(self, fid):
        return await self._one(WorkflowFolder, Q.GET_FOLDER_BY_ID, [fid])

    async def create_folder(
        self, fid, org_id, parent_id, name, desc, icon, sort_order, created_by
    ):
        await self.execute(
            Q.INSERT_FOLDER,
            [
                fid,
                org_id,
                parent_id,
                name,
                desc,
                icon,
                sort_order,
                created_by,
            ],
        )

    async def update_folder(self, fid, name, desc, icon, sort_order, parent_id):
        await self.execute(
            Q.UPDATE_FOLDER, [name, desc, icon, sort_order, parent_id, fid]
        )

    async def delete_folder(self, fid):
        await self.execute(Q.DELETE_FOLDER, [fid])

    # ── Schedules ─────────────────────────────────────────────
    async def get_schedules_by_workflow(self, workflow_id):
        return await self._many(
            WorkflowSchedule, Q.GET_SCHEDULES_BY_WORKFLOW, [workflow_id]
        )

    async def get_schedules_by_org(self, org_id):
        return await self._many(WorkflowSchedule, Q.GET_SCHEDULES_BY_ORG, [org_id])

    async def get_schedule(self, sid):
        return await self._one(WorkflowSchedule, Q.GET_SCHEDULE_BY_ID, [sid])

    async def get_due_schedules(self):
        return await self._many(WorkflowSchedule, Q.GET_DUE_SCHEDULES)

    async def create_schedule(
        self,
        sid,
        org_id,
        workflow_id,
        name,
        cron_expression,
        timezone,
        next_fire_at,
        created_by,
    ):
        await self.execute(
            Q.INSERT_SCHEDULE,
            [
                sid,
                org_id,
                workflow_id,
                name,
                cron_expression,
                timezone,
                next_fire_at,
                created_by,
            ],
        )

    async def update_schedule(
        self, sid, name, cron_expression, timezone, is_active, next_fire_at
    ):
        await self.execute(
            Q.UPDATE_SCHEDULE,
            [
                name,
                cron_expression,
                timezone,
                1 if is_active else 0,
                next_fire_at,
                sid,
            ],
        )

    async def record_schedule_fired(self, sid, next_fire_at):
        await self.execute(Q.UPDATE_SCHEDULE_FIRED, [next_fire_at, sid])

    async def delete_schedule(self, sid):
        await self.execute(Q.DELETE_SCHEDULE, [sid])

    # ── Audit log ─────────────────────────────────────────────
    async def get_audit_by_workflow(self, workflow_id, limit, offset):
        return await self._many(
            WorkflowAuditLog, Q.GET_AUDIT_BY_WORKFLOW, [workflow_id, limit, offset]
        )

    async def get_audit_by_org(self, org_id, limit, offset):
        return await self._many(
            WorkflowAuditLog, Q.GET_AUDIT_BY_ORG, [org_id, limit, offset]
        )

    async def log_audit(
        self,
        aid,
        org_id,
        workflow_id,
        run_id,
        actor_id,
        action,
        resource_type,
        resource_id,
        detail,
        ip_hash,
    ):
        await self.execute(
            Q.INSERT_AUDIT,
            [
                aid,
                org_id,
                workflow_id,
                run_id,
                actor_id,
                action,
                resource_type,
                resource_id,
                detail,
                ip_hash,
            ],
        )

    # ── Run costs ─────────────────────────────────────────────
    async def get_costs_by_run(self, run_id):
        return await self._many(WorkflowRunCost, Q.GET_COSTS_BY_RUN, [run_id])

    async def get_costs_by_workflow(self, workflow_id, limit, offset):
        return await self._many(
            WorkflowRunCost, Q.GET_COSTS_BY_WORKFLOW, [workflow_id, limit, offset]
        )

    async def create_run_cost(
        self,
        cid,
        run_id,
        step_id,
        workflow_id,
        org_id,
        node_type_id,
        cost_model,
        units_consumed,
        unit_label,
        cost_microcents,
        cost_actual_microcents,
        currency,
        external_ref,
        notes,
    ):
        await self.execute(
            Q.INSERT_RUN_COST,
            [
                cid,
                run_id,
                step_id,
                workflow_id,
                org_id,
                node_type_id,
                cost_model,
                units_consumed,
                unit_label,
                cost_microcents,
                cost_actual_microcents,
                currency,
                external_ref,
                notes,
            ],
        )

    async def get_cost_summary(self, workflow_id):
        row = await self.find_one(Q.GET_COST_SUMMARY, [workflow_id])
        return dict(row) if row else None

    # ── Promotions ────────────────────────────────────────────
    async def get_promotions(self, workflow_id):
        return await self._many(
            WorkflowPromotion, Q.GET_PROMOTIONS_BY_WORKFLOW, [workflow_id]
        )

    async def create_promotion(
        self,
        pid,
        workflow_id,
        org_id,
        from_env,
        to_env,
        version_number,
        promoted_by,
        approval_id,
        promotion_note,
    ):
        await self.execute(
            Q.INSERT_PROMOTION,
            [
                pid,
                workflow_id,
                org_id,
                from_env,
                to_env,
                version_number,
                promoted_by,
                approval_id,
                promotion_note,
            ],
        )

    async def update_promotion_status(self, pid, status):
        await self.execute(Q.UPDATE_PROMOTION_STATUS, [status, status, pid])
