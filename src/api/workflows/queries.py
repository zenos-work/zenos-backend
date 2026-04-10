"""SQL queries for the workflow module (Steps 20-22)."""

# ═══════════════════════════════════════════════════════════════
# Step 20 — Core builder
# ═══════════════════════════════════════════════════════════════

# ── Node types ────────────────────────────────────────────────
GET_NODE_TYPES = (
    "SELECT * FROM workflow_node_types WHERE is_active = 1 ORDER BY category, name"
)
GET_NODE_TYPES_BY_CATEGORY = "SELECT * FROM workflow_node_types WHERE is_active = 1 AND category = ? ORDER BY name"
GET_NODE_TYPE_BY_ID = "SELECT * FROM workflow_node_types WHERE id = ?"

# ── Workflows (core CRUD) ────────────────────────────────────
GET_WORKFLOWS_BY_ORG = """
    SELECT * FROM workflows WHERE org_id = ?
    ORDER BY updated_at DESC LIMIT ? OFFSET ?
"""
GET_WORKFLOWS_BY_OWNER = """
    SELECT * FROM workflows WHERE owner_id = ?
    ORDER BY updated_at DESC LIMIT ? OFFSET ?
"""
GET_WORKFLOWS_BY_ORG_AND_STATUS = """
    SELECT * FROM workflows WHERE org_id = ? AND status = ?
    ORDER BY updated_at DESC LIMIT ? OFFSET ?
"""
GET_WORKFLOW_BY_ID = "SELECT * FROM workflows WHERE id = ?"
COUNT_WORKFLOWS_BY_ORG = "SELECT count(*) as cnt FROM workflows WHERE org_id = ?"
COUNT_WORKFLOWS_BY_OWNER = "SELECT count(*) as cnt FROM workflows WHERE owner_id = ?"

INSERT_WORKFLOW = """
    INSERT INTO workflows (id, org_id, owner_id, name, description, status,
        environment, trigger_type, tags, scope_type, scope_filter, folder_id,
        approval_required)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_WORKFLOW = """
    UPDATE workflows SET name=?, description=?, status=?, environment=?,
        trigger_type=?, tags=?, scope_type=?, scope_filter=?, folder_id=?,
        approval_required=?, updated_at=datetime('now')
    WHERE id = ?
"""
DELETE_WORKFLOW = "DELETE FROM workflows WHERE id = ?"

UPDATE_WORKFLOW_STATUS = """
    UPDATE workflows SET status=?, updated_at=datetime('now') WHERE id = ?
"""
UPDATE_WORKFLOW_RUN_STATS = """
    UPDATE workflows SET total_runs = total_runs + 1,
        last_run_at = datetime('now'), last_run_status = ?,
        success_runs = CASE WHEN ? = 'success' THEN success_runs + 1 ELSE success_runs END,
        failed_runs = CASE WHEN ? = 'failed' THEN failed_runs + 1 ELSE failed_runs END,
        updated_at = datetime('now')
    WHERE id = ?
"""

# ── Workflow nodes ────────────────────────────────────────────
GET_NODES_BY_WORKFLOW = (
    "SELECT * FROM workflow_nodes WHERE workflow_id = ? ORDER BY created_at"
)
GET_NODE_BY_ID = "SELECT * FROM workflow_nodes WHERE id = ?"
INSERT_NODE = """
    INSERT INTO workflow_nodes (id, workflow_id, node_type_id, label,
        position_x, position_y, display_config, connector_binding_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_NODE = """
    UPDATE workflow_nodes SET label=?, position_x=?, position_y=?,
        display_config=?, connector_binding_id=?
    WHERE id = ?
"""
DELETE_NODE = "DELETE FROM workflow_nodes WHERE id = ?"

# ── Workflow edges ────────────────────────────────────────────
GET_EDGES_BY_WORKFLOW = "SELECT * FROM workflow_edges WHERE workflow_id = ?"
GET_EDGE_BY_ID = "SELECT * FROM workflow_edges WHERE id = ?"
INSERT_EDGE = """
    INSERT INTO workflow_edges (id, workflow_id, source_node_id,
        target_node_id, condition_label)
    VALUES (?, ?, ?, ?, ?)
"""
DELETE_EDGE = "DELETE FROM workflow_edges WHERE id = ?"

# ── Versions ──────────────────────────────────────────────────
GET_VERSIONS_BY_WORKFLOW = """
    SELECT * FROM workflow_versions WHERE workflow_id = ?
    ORDER BY version_number DESC
"""
GET_VERSION_BY_ID = "SELECT * FROM workflow_versions WHERE id = ?"
GET_LATEST_VERSION = """
    SELECT * FROM workflow_versions WHERE workflow_id = ?
    ORDER BY version_number DESC LIMIT 1
"""
INSERT_VERSION = """
    INSERT INTO workflow_versions (id, workflow_id, version_number,
        definition, changelog, created_by)
    VALUES (?, ?, ?, ?, ?, ?)
"""

# ── Webhooks ──────────────────────────────────────────────────
GET_WEBHOOKS_BY_WORKFLOW = "SELECT * FROM workflow_webhooks WHERE workflow_id = ?"
GET_WEBHOOK_BY_TOKEN = (
    "SELECT * FROM workflow_webhooks WHERE token = ? AND is_active = 1"
)
GET_WEBHOOK_BY_ID = "SELECT * FROM workflow_webhooks WHERE id = ?"
INSERT_WEBHOOK = """
    INSERT INTO workflow_webhooks (id, workflow_id, node_id, token, method)
    VALUES (?, ?, ?, ?, ?)
"""
UPDATE_WEBHOOK_HIT = """
    UPDATE workflow_webhooks SET hit_count = hit_count + 1,
        last_hit_at = datetime('now')
    WHERE id = ?
"""
DELETE_WEBHOOK = "DELETE FROM workflow_webhooks WHERE id = ?"

# ── Templates ─────────────────────────────────────────────────
GET_TEMPLATES = """
    SELECT tl.*, w.trigger_type, w.tags
    FROM workflow_template_listings tl
    JOIN workflows w ON w.id = tl.workflow_id
    WHERE tl.is_public = 1
    ORDER BY tl.download_count DESC LIMIT ? OFFSET ?
"""
GET_TEMPLATES_BY_CATEGORY = """
    SELECT tl.*, w.trigger_type, w.tags
    FROM workflow_template_listings tl
    JOIN workflows w ON w.id = tl.workflow_id
    WHERE tl.is_public = 1 AND tl.category = ?
    ORDER BY tl.download_count DESC LIMIT ? OFFSET ?
"""
GET_TEMPLATE_BY_ID = "SELECT * FROM workflow_template_listings WHERE id = ?"
INSERT_TEMPLATE = """
    INSERT INTO workflow_template_listings (id, workflow_id, title,
        short_desc, category, use_case_tags, preview_image)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_TEMPLATE_DOWNLOAD = """
    UPDATE workflow_template_listings SET download_count = download_count + 1
    WHERE id = ?
"""

# ── Integrations ──────────────────────────────────────────────
GET_INTEGRATIONS_BY_ORG = (
    "SELECT * FROM workflow_integrations WHERE org_id = ? ORDER BY created_at DESC"
)
GET_INTEGRATION_BY_ID = "SELECT * FROM workflow_integrations WHERE id = ?"
INSERT_INTEGRATION = """
    INSERT INTO workflow_integrations (id, org_id, integration_type, name,
        kv_secret_key, created_by)
    VALUES (?, ?, ?, ?, ?, ?)
"""
DELETE_INTEGRATION = "DELETE FROM workflow_integrations WHERE id = ?"


# ═══════════════════════════════════════════════════════════════
# Step 21 — Execution engine
# ═══════════════════════════════════════════════════════════════

GET_RUNS_BY_WORKFLOW = """
    SELECT * FROM workflow_runs WHERE workflow_id = ?
    ORDER BY started_at DESC LIMIT ? OFFSET ?
"""
GET_RUN_BY_ID = "SELECT * FROM workflow_runs WHERE id = ?"
COUNT_RUNS_BY_WORKFLOW = (
    "SELECT count(*) as cnt FROM workflow_runs WHERE workflow_id = ?"
)
INSERT_RUN = """
    INSERT INTO workflow_runs (id, workflow_id, triggered_by, trigger_payload,
        status, steps_total)
    VALUES (?, ?, ?, ?, 'running', ?)
"""
UPDATE_RUN_STATUS = """
    UPDATE workflow_runs SET status=?, finished_at=datetime('now'),
        duration_ms=?, error_message=?,
        steps_succeeded=?, steps_failed=?,
        final_context=?
    WHERE id = ?
"""
CANCEL_RUN = """
    UPDATE workflow_runs SET status='cancelled', finished_at=datetime('now')
    WHERE id = ? AND status = 'running'
"""
SET_RUN_WAITING = """
    UPDATE workflow_runs SET waiting_for_task_id = ? WHERE id = ?
"""

GET_RUN_STEPS = "SELECT * FROM workflow_run_steps WHERE run_id = ? ORDER BY started_at"
GET_RUN_STEP_BY_ID = "SELECT * FROM workflow_run_steps WHERE id = ?"
INSERT_RUN_STEP = """
    INSERT INTO workflow_run_steps (id, run_id, node_id, node_type_id,
        status, attempt, input_data)
    VALUES (?, ?, ?, ?, 'pending', ?, ?)
"""
UPDATE_RUN_STEP = """
    UPDATE workflow_run_steps SET status=?, output_data=?,
        error_message=?, started_at=COALESCE(started_at, datetime('now')),
        finished_at=CASE WHEN ? IN ('success','failed','skipped') THEN datetime('now') ELSE finished_at END,
        duration_ms=?
    WHERE id = ?
"""


# ═══════════════════════════════════════════════════════════════
# Step 22 — HITL + Enterprise
# ═══════════════════════════════════════════════════════════════

# ── Human tasks ───────────────────────────────────────────────
GET_TASKS_BY_USER = """
    SELECT * FROM workflow_human_tasks
    WHERE (assigned_to = ? OR assigned_role IN (SELECT role FROM users WHERE id = ?))
    AND status IN ('pending', 'in_review')
    ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
             created_at ASC
    LIMIT ? OFFSET ?
"""
GET_TASKS_BY_ORG = """
    SELECT * FROM workflow_human_tasks WHERE org_id = ?
    ORDER BY created_at DESC LIMIT ? OFFSET ?
"""
GET_TASK_BY_ID = "SELECT * FROM workflow_human_tasks WHERE id = ?"
INSERT_TASK = """
    INSERT INTO workflow_human_tasks (id, run_id, step_id, workflow_id, org_id,
        assigned_to, assigned_role, assigned_team_id,
        task_title, instruction_text, input_data, editable_data,
        context_snapshot, priority, deadline_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_TASK_DECISION = """
    UPDATE workflow_human_tasks SET status=?, decision=?,
        reviewer_id=?, reviewer_note=?, output_data=?,
        completed_at=datetime('now')
    WHERE id = ?
"""
UPDATE_TASK_START_REVIEW = """
    UPDATE workflow_human_tasks SET status='in_review',
        reviewer_id=?, started_review_at=datetime('now')
    WHERE id = ? AND status = 'pending'
"""

# ── Approvals ─────────────────────────────────────────────────
GET_APPROVALS_BY_WORKFLOW = """
    SELECT * FROM workflow_approvals WHERE workflow_id = ?
    ORDER BY created_at DESC
"""
GET_APPROVAL_BY_ID = "SELECT * FROM workflow_approvals WHERE id = ?"
GET_PENDING_APPROVALS_FOR_USER = """
    SELECT * FROM workflow_approvals
    WHERE (assigned_to = ? OR assigned_to IS NULL)
    AND status = 'pending'
    ORDER BY created_at ASC
"""
INSERT_APPROVAL = """
    INSERT INTO workflow_approvals (id, workflow_id, version_number,
        requested_by, assigned_to, request_note, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_APPROVAL = """
    UPDATE workflow_approvals SET status=?, review_note=?,
        reviewed_by=?, reviewed_at=datetime('now'),
        updated_at=datetime('now')
    WHERE id = ?
"""

# ── Content bindings ──────────────────────────────────────────
GET_BINDINGS_BY_WORKFLOW = (
    "SELECT * FROM workflow_content_bindings WHERE workflow_id = ?"
)
GET_BINDINGS_BY_ORG = """
    SELECT * FROM workflow_content_bindings
    WHERE org_id = ? AND is_active = 1
    ORDER BY priority ASC
"""
GET_BINDING_BY_ID = "SELECT * FROM workflow_content_bindings WHERE id = ?"
INSERT_BINDING = """
    INSERT INTO workflow_content_bindings (id, workflow_id, org_id,
        bind_type, bind_criteria, trigger_event, priority, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_BINDING = """
    UPDATE workflow_content_bindings SET bind_type=?, bind_criteria=?,
        trigger_event=?, priority=?, is_active=?,
        updated_at=datetime('now')
    WHERE id = ?
"""
DELETE_BINDING = "DELETE FROM workflow_content_bindings WHERE id = ?"

# ── Permissions ───────────────────────────────────────────────
GET_PERMISSIONS_BY_WORKFLOW = "SELECT * FROM workflow_permissions WHERE workflow_id = ?"
GET_PERMISSIONS_FOR_USER = """
    SELECT * FROM workflow_permissions
    WHERE workflow_id = ? AND (
        (grantee_type = 'user' AND grantee_id = ?)
        OR (grantee_type = 'org_role' AND grantee_id = ?)
    )
"""
INSERT_PERMISSION = """
    INSERT INTO workflow_permissions (id, workflow_id, grantee_type,
        grantee_id, permission, granted_by)
    VALUES (?, ?, ?, ?, ?, ?)
"""
DELETE_PERMISSION = "DELETE FROM workflow_permissions WHERE id = ?"

# ── Run messages ──────────────────────────────────────────────
GET_MESSAGES_BY_RUN = """
    SELECT * FROM workflow_run_messages WHERE run_id = ?
    ORDER BY created_at ASC
"""
INSERT_MESSAGE = """
    INSERT INTO workflow_run_messages (id, run_id, workflow_id, step_id,
        task_id, sender_id, sender_role, content, message_type,
        attachment_url, attachment_type, is_internal)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ── Policies ──────────────────────────────────────────────────
GET_POLICIES_BY_ORG = """
    SELECT * FROM workflow_policies WHERE org_id = ? AND is_active = 1
"""
GET_POLICY_BY_ID = "SELECT * FROM workflow_policies WHERE id = ?"
INSERT_POLICY = """
    INSERT INTO workflow_policies (id, org_id, policy_type, policy_value,
        enforced_by, created_by)
    VALUES (?, ?, ?, ?, ?, ?)
"""
UPDATE_POLICY = """
    UPDATE workflow_policies SET policy_value=?, is_active=?,
        updated_at=datetime('now')
    WHERE id = ?
"""

# ── Folders ───────────────────────────────────────────────────
GET_FOLDERS_BY_ORG = """
    SELECT * FROM workflow_folders WHERE org_id = ?
    ORDER BY sort_order, name
"""
GET_FOLDER_BY_ID = "SELECT * FROM workflow_folders WHERE id = ?"
INSERT_FOLDER = """
    INSERT INTO workflow_folders (id, org_id, parent_id, name,
        description, icon, sort_order, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_FOLDER = """
    UPDATE workflow_folders SET name=?, description=?, icon=?,
        sort_order=?, parent_id=?
    WHERE id = ?
"""
DELETE_FOLDER = "DELETE FROM workflow_folders WHERE id = ?"

# ── Schedules ─────────────────────────────────────────────────
GET_SCHEDULES_BY_WORKFLOW = "SELECT * FROM workflow_schedules WHERE workflow_id = ?"
GET_SCHEDULES_BY_ORG = """
    SELECT * FROM workflow_schedules WHERE org_id = ?
    ORDER BY created_at DESC
"""
GET_SCHEDULE_BY_ID = "SELECT * FROM workflow_schedules WHERE id = ?"
GET_DUE_SCHEDULES = """
    SELECT * FROM workflow_schedules
    WHERE is_active = 1 AND next_fire_at <= datetime('now')
    ORDER BY next_fire_at ASC
"""
INSERT_SCHEDULE = """
    INSERT INTO workflow_schedules (id, org_id, workflow_id, name,
        cron_expression, timezone, next_fire_at, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_SCHEDULE = """
    UPDATE workflow_schedules SET name=?, cron_expression=?, timezone=?,
        is_active=?, next_fire_at=?, updated_at=datetime('now')
    WHERE id = ?
"""
UPDATE_SCHEDULE_FIRED = """
    UPDATE workflow_schedules SET last_fired_at = datetime('now'),
        fire_count = fire_count + 1, next_fire_at = ?,
        updated_at = datetime('now')
    WHERE id = ?
"""
DELETE_SCHEDULE = "DELETE FROM workflow_schedules WHERE id = ?"

# ── Audit log ─────────────────────────────────────────────────
GET_AUDIT_BY_WORKFLOW = """
    SELECT * FROM workflow_audit_log WHERE workflow_id = ?
    ORDER BY created_at DESC LIMIT ? OFFSET ?
"""
GET_AUDIT_BY_ORG = """
    SELECT * FROM workflow_audit_log WHERE org_id = ?
    ORDER BY created_at DESC LIMIT ? OFFSET ?
"""
INSERT_AUDIT = """
    INSERT INTO workflow_audit_log (id, org_id, workflow_id, run_id,
        actor_id, action, resource_type, resource_id, detail, ip_hash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# ── Run costs ─────────────────────────────────────────────────
GET_COSTS_BY_RUN = "SELECT * FROM workflow_run_costs WHERE run_id = ?"
GET_COSTS_BY_WORKFLOW = """
    SELECT * FROM workflow_run_costs WHERE workflow_id = ?
    ORDER BY created_at DESC LIMIT ? OFFSET ?
"""
INSERT_RUN_COST = """
    INSERT INTO workflow_run_costs (id, run_id, step_id, workflow_id,
        org_id, node_type_id, cost_model, units_consumed, unit_label,
        cost_microcents, cost_actual_microcents, currency, external_ref, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
GET_COST_SUMMARY = "SELECT * FROM workflow_cost_summary WHERE workflow_id = ?"

# ── Promotions ────────────────────────────────────────────────
GET_PROMOTIONS_BY_WORKFLOW = """
    SELECT * FROM workflow_promotions WHERE workflow_id = ?
    ORDER BY created_at DESC
"""
INSERT_PROMOTION = """
    INSERT INTO workflow_promotions (id, workflow_id, org_id,
        from_environment, to_environment, version_number,
        promoted_by, approval_id, promotion_note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
UPDATE_PROMOTION_STATUS = """
    UPDATE workflow_promotions SET status=?,
        promoted_at=CASE WHEN ? = 'promoted' THEN datetime('now') ELSE promoted_at END
    WHERE id = ?
"""
