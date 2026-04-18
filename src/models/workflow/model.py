"""Workflow models covering tables from 0028, 0034, and 0035 SQL schemas."""

import json
from dataclasses import dataclass
from models.base import BaseModel


def _json_field(row, key, default=None):
    val = row.get(key)
    if val is None:
        return default if default is not None else {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}


# ── Step 20: Core ──────────────────────────────────────────────


@dataclass
class WorkflowNodeType(BaseModel):
    id: str = ""
    category: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    config_schema: dict = None
    output_schema: dict = None
    is_enterprise: bool = False
    is_active: bool = True
    connector_definition_id: str = ""
    connector_action_id: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            category=row.get("category", ""),
            name=row.get("name", ""),
            description=row.get("description") or "",
            icon=row.get("icon") or "",
            config_schema=_json_field(row, "config_schema", {}),
            output_schema=_json_field(row, "output_schema", {}),
            is_enterprise=bool(row.get("is_enterprise", 0)),
            is_active=bool(row.get("is_active", 1)),
            connector_definition_id=row.get("connector_definition_id") or "",
            connector_action_id=row.get("connector_action_id") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "category": self.category,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "config_schema": self.config_schema,
            "output_schema": self.output_schema,
            "is_enterprise": self.is_enterprise,
            "is_active": self.is_active,
        }
        if scope == "admin":
            d["connector_definition_id"] = self.connector_definition_id
            d["connector_action_id"] = self.connector_action_id
            d["created_at"] = self.created_at
        return d


@dataclass
class Workflow(BaseModel):
    id: str = ""
    org_id: str = ""
    owner_id: str = ""
    name: str = ""
    description: str = ""
    status: str = "draft"
    environment: str = "dev"
    trigger_type: str = ""
    definition_version: int = 1
    total_runs: int = 0
    success_runs: int = 0
    failed_runs: int = 0
    last_run_at: str = ""
    last_run_status: str = ""
    is_template: bool = False
    template_category: str = ""
    cloned_from: str = ""
    tags: list = None
    approval_status: str = "not_required"
    approval_required: bool = False
    approved_by: str = ""
    approved_at: str = ""
    approval_note: str = ""
    scope_type: str = "manual"
    scope_filter: dict = None
    folder_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id") or "",
            owner_id=row.get("owner_id", ""),
            name=row.get("name", ""),
            description=row.get("description") or "",
            status=row.get("status", "draft"),
            environment=row.get("environment", "dev"),
            trigger_type=row.get("trigger_type", ""),
            definition_version=row.get("definition_version", 1),
            total_runs=row.get("total_runs", 0),
            success_runs=row.get("success_runs", 0),
            failed_runs=row.get("failed_runs", 0),
            last_run_at=row.get("last_run_at") or "",
            last_run_status=row.get("last_run_status") or "",
            is_template=bool(row.get("is_template", 0)),
            template_category=row.get("template_category") or "",
            cloned_from=row.get("cloned_from") or "",
            tags=_json_field(row, "tags", []),
            approval_status=row.get("approval_status") or "not_required",
            approval_required=bool(row.get("approval_required", 0)),
            approved_by=row.get("approved_by") or "",
            approved_at=row.get("approved_at") or "",
            approval_note=row.get("approval_note") or "",
            scope_type=row.get("scope_type", "manual"),
            scope_filter=_json_field(row, "scope_filter", {}),
            folder_id=row.get("folder_id") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "environment": self.environment,
            "trigger_type": self.trigger_type,
            "definition_version": self.definition_version,
            "total_runs": self.total_runs,
            "success_runs": self.success_runs,
            "failed_runs": self.failed_runs,
            "last_run_at": self.last_run_at,
            "last_run_status": self.last_run_status,
            "is_template": self.is_template,
            "tags": self.tags,
            "scope_type": self.scope_type,
            "folder_id": self.folder_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d.update(
                {
                    "template_category": self.template_category,
                    "cloned_from": self.cloned_from,
                    "approval_status": self.approval_status,
                    "approval_required": self.approval_required,
                    "approved_by": self.approved_by,
                    "approved_at": self.approved_at,
                    "approval_note": self.approval_note,
                    "scope_filter": self.scope_filter,
                }
            )
        return d


@dataclass
class WorkflowVersion(BaseModel):
    id: str = ""
    workflow_id: str = ""
    version_number: int = 0
    definition: dict = None
    changelog: str = ""
    created_by: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            version_number=row.get("version_number", 0),
            definition=_json_field(row, "definition", {}),
            changelog=row.get("changelog") or "",
            created_by=row.get("created_by", ""),
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "definition": self.definition,
            "changelog": self.changelog,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowNode(BaseModel):
    id: str = ""
    workflow_id: str = ""
    node_type_id: str = ""
    label: str = ""
    position_x: float = 0.0
    position_y: float = 0.0
    display_config: dict = None
    connector_binding_id: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            node_type_id=row.get("node_type_id", ""),
            label=row.get("label") or "",
            position_x=float(row.get("position_x", 0)),
            position_y=float(row.get("position_y", 0)),
            display_config=_json_field(row, "display_config", {}),
            connector_binding_id=row.get("connector_binding_id") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "node_type_id": self.node_type_id,
            "label": self.label,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "display_config": self.display_config,
            "connector_binding_id": self.connector_binding_id,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowEdge(BaseModel):
    id: str = ""
    workflow_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    condition_label: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            source_node_id=row.get("source_node_id", ""),
            target_node_id=row.get("target_node_id", ""),
            condition_label=row.get("condition_label") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "condition_label": self.condition_label,
        }


@dataclass
class WorkflowWebhook(BaseModel):
    id: str = ""
    workflow_id: str = ""
    node_id: str = ""
    token: str = ""
    method: str = "POST"
    is_active: bool = True
    last_hit_at: str = ""
    hit_count: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            node_id=row.get("node_id") or "",
            token=row.get("token", ""),
            method=row.get("method", "POST"),
            is_active=bool(row.get("is_active", 1)),
            last_hit_at=row.get("last_hit_at") or "",
            hit_count=row.get("hit_count", 0),
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "token": self.token,
            "method": self.method,
            "is_active": self.is_active,
            "last_hit_at": self.last_hit_at,
            "hit_count": self.hit_count,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowIntegration(BaseModel):
    id: str = ""
    org_id: str = ""
    integration_type: str = ""
    name: str = ""
    kv_secret_key: str = ""
    is_active: bool = True
    last_tested_at: str = ""
    created_by: str = ""
    connector_instance_id: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            integration_type=row.get("integration_type", ""),
            name=row.get("name", ""),
            kv_secret_key=row.get("kv_secret_key", ""),
            is_active=bool(row.get("is_active", 1)),
            last_tested_at=row.get("last_tested_at") or "",
            created_by=row.get("created_by", ""),
            connector_instance_id=row.get("connector_instance_id") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "org_id": self.org_id,
            "integration_type": self.integration_type,
            "name": self.name,
            "is_active": self.is_active,
            "last_tested_at": self.last_tested_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if scope == "admin":
            d["kv_secret_key"] = self.kv_secret_key
            d["created_by"] = self.created_by
            d["connector_instance_id"] = self.connector_instance_id
        return d


@dataclass
class WorkflowTemplateListing(BaseModel):
    id: str = ""
    workflow_id: str = ""
    title: str = ""
    short_desc: str = ""
    category: str = ""
    use_case_tags: list = None
    preview_image: str = ""
    is_public: bool = True
    download_count: int = 0
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            title=row.get("title", ""),
            short_desc=row.get("short_desc", ""),
            category=row.get("category", ""),
            use_case_tags=_json_field(row, "use_case_tags", []),
            preview_image=row.get("preview_image") or "",
            is_public=bool(row.get("is_public", 1)),
            download_count=row.get("download_count", 0),
            rating_avg=float(row.get("rating_avg", 0)),
            rating_count=row.get("rating_count", 0),
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "title": self.title,
            "short_desc": self.short_desc,
            "category": self.category,
            "use_case_tags": self.use_case_tags,
            "preview_image": self.preview_image,
            "is_public": self.is_public,
            "download_count": self.download_count,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "created_at": self.created_at,
        }


# ── Step 21: Execution ─────────────────────────────────────────


@dataclass
class WorkflowRun(BaseModel):
    id: str = ""
    workflow_id: str = ""
    triggered_by: str = ""
    trigger_payload: dict = None
    status: str = "running"
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    steps_total: int = 0
    steps_succeeded: int = 0
    steps_failed: int = 0
    error_message: str = ""
    final_context: dict = None
    waiting_for_task_id: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            triggered_by=row.get("triggered_by") or "",
            trigger_payload=_json_field(row, "trigger_payload", {}),
            status=row.get("status", "running"),
            started_at=row.get("started_at") or "",
            finished_at=row.get("finished_at") or "",
            duration_ms=row.get("duration_ms") or 0,
            steps_total=row.get("steps_total", 0),
            steps_succeeded=row.get("steps_succeeded", 0),
            steps_failed=row.get("steps_failed", 0),
            error_message=row.get("error_message") or "",
            final_context=_json_field(row, "final_context", {}),
            waiting_for_task_id=row.get("waiting_for_task_id") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "triggered_by": self.triggered_by,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "steps_total": self.steps_total,
            "steps_succeeded": self.steps_succeeded,
            "steps_failed": self.steps_failed,
            "error_message": self.error_message,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d["trigger_payload"] = self.trigger_payload
            d["final_context"] = self.final_context
            d["waiting_for_task_id"] = self.waiting_for_task_id
        return d


@dataclass
class WorkflowRunStep(BaseModel):
    id: str = ""
    run_id: str = ""
    node_id: str = ""
    node_type_id: str = ""
    status: str = "pending"
    attempt: int = 1
    input_data: dict = None
    output_data: dict = None
    error_message: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            run_id=row.get("run_id", ""),
            node_id=row.get("node_id", ""),
            node_type_id=row.get("node_type_id", ""),
            status=row.get("status", "pending"),
            attempt=row.get("attempt", 1),
            input_data=_json_field(row, "input_data", {}),
            output_data=_json_field(row, "output_data", {}),
            error_message=row.get("error_message") or "",
            started_at=row.get("started_at") or "",
            finished_at=row.get("finished_at") or "",
            duration_ms=row.get("duration_ms") or 0,
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "node_type_id": self.node_type_id,
            "status": self.status,
            "attempt": self.attempt,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
        }


# ── Step 22: HITL + Enterprise ─────────────────────────────────


@dataclass
class WorkflowApproval(BaseModel):
    id: str = ""
    workflow_id: str = ""
    version_number: int = 0
    requested_by: str = ""
    assigned_to: str = ""
    status: str = "pending"
    request_note: str = ""
    review_note: str = ""
    reviewed_by: str = ""
    reviewed_at: str = ""
    expires_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            version_number=row.get("version_number", 0),
            requested_by=row.get("requested_by", ""),
            assigned_to=row.get("assigned_to") or "",
            status=row.get("status", "pending"),
            request_note=row.get("request_note") or "",
            review_note=row.get("review_note") or "",
            reviewed_by=row.get("reviewed_by") or "",
            reviewed_at=row.get("reviewed_at") or "",
            expires_at=row.get("expires_at") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "version_number": self.version_number,
            "requested_by": self.requested_by,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "request_note": self.request_note,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowHumanTask(BaseModel):
    id: str = ""
    run_id: str = ""
    step_id: str = ""
    workflow_id: str = ""
    org_id: str = ""
    assigned_to: str = ""
    assigned_role: str = ""
    assigned_team_id: str = ""
    task_title: str = ""
    instruction_text: str = ""
    input_data: dict = None
    editable_data: dict = None
    context_snapshot: dict = None
    status: str = "pending"
    decision: str = ""
    reviewer_id: str = ""
    reviewer_note: str = ""
    output_data: dict = None
    priority: str = "normal"
    deadline_at: str = ""
    started_review_at: str = ""
    completed_at: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            run_id=row.get("run_id", ""),
            step_id=row.get("step_id") or "",
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id") or "",
            assigned_to=row.get("assigned_to") or "",
            assigned_role=row.get("assigned_role") or "",
            assigned_team_id=row.get("assigned_team_id") or "",
            task_title=row.get("task_title", ""),
            instruction_text=row.get("instruction_text") or "",
            input_data=_json_field(row, "input_data", {}),
            editable_data=_json_field(row, "editable_data", {}),
            context_snapshot=_json_field(row, "context_snapshot", {}),
            status=row.get("status", "pending"),
            decision=row.get("decision") or "",
            reviewer_id=row.get("reviewer_id") or "",
            reviewer_note=row.get("reviewer_note") or "",
            output_data=_json_field(row, "output_data", {}),
            priority=row.get("priority", "normal"),
            deadline_at=row.get("deadline_at") or "",
            started_review_at=row.get("started_review_at") or "",
            completed_at=row.get("completed_at") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "workflow_id": self.workflow_id,
            "org_id": self.org_id,
            "task_title": self.task_title,
            "instruction_text": self.instruction_text,
            "input_data": self.input_data,
            "editable_data": self.editable_data,
            "status": self.status,
            "decision": self.decision,
            "priority": self.priority,
            "deadline_at": self.deadline_at,
            "created_at": self.created_at,
        }
        if scope == "admin":
            d.update(
                {
                    "assigned_to": self.assigned_to,
                    "assigned_role": self.assigned_role,
                    "assigned_team_id": self.assigned_team_id,
                    "context_snapshot": self.context_snapshot,
                    "reviewer_id": self.reviewer_id,
                    "reviewer_note": self.reviewer_note,
                    "output_data": self.output_data,
                    "started_review_at": self.started_review_at,
                    "completed_at": self.completed_at,
                }
            )
        return d


@dataclass
class WorkflowContentBinding(BaseModel):
    id: str = ""
    workflow_id: str = ""
    org_id: str = ""
    bind_type: str = "all_org_content"
    bind_criteria: dict = None
    trigger_event: str = "on_submit"
    priority: int = 100
    is_active: bool = True
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id") or "",
            bind_type=row.get("bind_type", "all_org_content"),
            bind_criteria=_json_field(row, "bind_criteria", {}),
            trigger_event=row.get("trigger_event", "on_submit"),
            priority=row.get("priority", 100),
            is_active=bool(row.get("is_active", 1)),
            created_by=row.get("created_by") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "org_id": self.org_id,
            "bind_type": self.bind_type,
            "bind_criteria": self.bind_criteria,
            "trigger_event": self.trigger_event,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowPermission(BaseModel):
    id: str = ""
    workflow_id: str = ""
    grantee_type: str = ""
    grantee_id: str = ""
    permission: str = ""
    granted_by: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            grantee_type=row.get("grantee_type", ""),
            grantee_id=row.get("grantee_id", ""),
            permission=row.get("permission", ""),
            granted_by=row.get("granted_by") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "grantee_type": self.grantee_type,
            "grantee_id": self.grantee_id,
            "permission": self.permission,
            "granted_by": self.granted_by,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowRunMessage(BaseModel):
    id: str = ""
    run_id: str = ""
    workflow_id: str = ""
    step_id: str = ""
    task_id: str = ""
    sender_id: str = ""
    sender_role: str = "author"
    content: str = ""
    message_type: str = "comment"
    attachment_url: str = ""
    attachment_type: str = ""
    is_internal: bool = False
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            run_id=row.get("run_id", ""),
            workflow_id=row.get("workflow_id", ""),
            step_id=row.get("step_id") or "",
            task_id=row.get("task_id") or "",
            sender_id=row.get("sender_id", ""),
            sender_role=row.get("sender_role", "author"),
            content=row.get("content", ""),
            message_type=row.get("message_type", "comment"),
            attachment_url=row.get("attachment_url") or "",
            attachment_type=row.get("attachment_type") or "",
            is_internal=bool(row.get("is_internal", 0)),
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        d = {
            "id": self.id,
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "sender_id": self.sender_id,
            "sender_role": self.sender_role,
            "content": self.content,
            "message_type": self.message_type,
            "created_at": self.created_at,
        }
        if self.attachment_url:
            d["attachment_url"] = self.attachment_url
            d["attachment_type"] = self.attachment_type
        if scope == "admin":
            d["step_id"] = self.step_id
            d["task_id"] = self.task_id
            d["is_internal"] = self.is_internal
        return d


@dataclass
class WorkflowPolicy(BaseModel):
    id: str = ""
    org_id: str = ""
    policy_type: str = ""
    policy_value: dict = None
    is_active: bool = True
    enforced_by: str = "system"
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            policy_type=row.get("policy_type", ""),
            policy_value=_json_field(row, "policy_value", {}),
            is_active=bool(row.get("is_active", 1)),
            enforced_by=row.get("enforced_by", "system"),
            created_by=row.get("created_by") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "policy_type": self.policy_type,
            "policy_value": self.policy_value,
            "is_active": self.is_active,
            "enforced_by": self.enforced_by,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowFolder(BaseModel):
    id: str = ""
    org_id: str = ""
    parent_id: str = ""
    name: str = ""
    description: str = ""
    icon: str = ""
    sort_order: int = 0
    created_by: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            parent_id=row.get("parent_id") or "",
            name=row.get("name", ""),
            description=row.get("description") or "",
            icon=row.get("icon") or "",
            sort_order=row.get("sort_order", 0),
            created_by=row.get("created_by") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowSchedule(BaseModel):
    id: str = ""
    org_id: str = ""
    workflow_id: str = ""
    name: str = ""
    cron_expression: str = ""
    timezone: str = "UTC"
    is_active: bool = True
    last_fired_at: str = ""
    next_fire_at: str = ""
    fire_count: int = 0
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id", ""),
            workflow_id=row.get("workflow_id", ""),
            name=row.get("name", ""),
            cron_expression=row.get("cron_expression", ""),
            timezone=row.get("timezone", "UTC"),
            is_active=bool(row.get("is_active", 1)),
            last_fired_at=row.get("last_fired_at") or "",
            next_fire_at=row.get("next_fire_at") or "",
            fire_count=row.get("fire_count", 0),
            created_by=row.get("created_by") or "",
            created_at=row.get("created_at") or "",
            updated_at=row.get("updated_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "last_fired_at": self.last_fired_at,
            "next_fire_at": self.next_fire_at,
            "fire_count": self.fire_count,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class WorkflowAuditLog(BaseModel):
    id: str = ""
    org_id: str = ""
    workflow_id: str = ""
    run_id: str = ""
    actor_id: str = ""
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    detail: dict = None
    ip_hash: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            org_id=row.get("org_id") or "",
            workflow_id=row.get("workflow_id") or "",
            run_id=row.get("run_id") or "",
            actor_id=row.get("actor_id") or "",
            action=row.get("action", ""),
            resource_type=row.get("resource_type") or "",
            resource_id=row.get("resource_id") or "",
            detail=_json_field(row, "detail", {}),
            ip_hash=row.get("ip_hash") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "workflow_id": self.workflow_id,
            "run_id": self.run_id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "detail": self.detail,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowRunCost(BaseModel):
    id: str = ""
    run_id: str = ""
    step_id: str = ""
    workflow_id: str = ""
    org_id: str = ""
    node_type_id: str = ""
    cost_model: str = ""
    units_consumed: float = 0.0
    unit_label: str = ""
    cost_microcents: int = 0
    cost_actual_microcents: int = 0
    currency: str = "USD"
    external_ref: str = ""
    notes: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            run_id=row.get("run_id", ""),
            step_id=row.get("step_id") or "",
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id") or "",
            node_type_id=row.get("node_type_id", ""),
            cost_model=row.get("cost_model", ""),
            units_consumed=float(row.get("units_consumed") or 0),
            unit_label=row.get("unit_label") or "",
            cost_microcents=row.get("cost_microcents", 0),
            cost_actual_microcents=row.get("cost_actual_microcents") or 0,
            currency=row.get("currency", "USD"),
            external_ref=row.get("external_ref") or "",
            notes=row.get("notes") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "workflow_id": self.workflow_id,
            "node_type_id": self.node_type_id,
            "cost_model": self.cost_model,
            "units_consumed": self.units_consumed,
            "unit_label": self.unit_label,
            "cost_microcents": self.cost_microcents,
            "currency": self.currency,
            "created_at": self.created_at,
        }


@dataclass
class WorkflowPromotion(BaseModel):
    id: str = ""
    workflow_id: str = ""
    org_id: str = ""
    from_environment: str = ""
    to_environment: str = ""
    version_number: int = 0
    promoted_by: str = ""
    approval_id: str = ""
    status: str = "pending"
    rollback_version: int = 0
    promotion_note: str = ""
    promoted_at: str = ""
    created_at: str = ""

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row.get("id", ""),
            workflow_id=row.get("workflow_id", ""),
            org_id=row.get("org_id") or "",
            from_environment=row.get("from_environment", ""),
            to_environment=row.get("to_environment", ""),
            version_number=row.get("version_number", 0),
            promoted_by=row.get("promoted_by", ""),
            approval_id=row.get("approval_id") or "",
            status=row.get("status", "pending"),
            rollback_version=row.get("rollback_version") or 0,
            promotion_note=row.get("promotion_note") or "",
            promoted_at=row.get("promoted_at") or "",
            created_at=row.get("created_at") or "",
        )

    def to_dict(self, scope="public"):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "org_id": self.org_id,
            "from_environment": self.from_environment,
            "to_environment": self.to_environment,
            "version_number": self.version_number,
            "promoted_by": self.promoted_by,
            "status": self.status,
            "promotion_note": self.promotion_note,
            "promoted_at": self.promoted_at,
            "created_at": self.created_at,
        }
