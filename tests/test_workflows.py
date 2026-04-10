"""Tests for Phase 4 — Workflow Orchestrator (model + service + handler)."""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

if "js" not in sys.modules:
    js_stub = types.ModuleType("js")

    class _Headers:
        @staticmethod
        def new(values=None, **_kwargs):
            return (
                dict(values)
                if isinstance(values, dict)
                else ({} if values is None else {k: v for k, v in values})
            )

    class _Resp:
        def __init__(self, body=None, status=200, headers=None):
            self.status_code = status
            self.headers = headers or {}
            self._body = body

        def json(self):
            if self._body is None or self._body == "":
                return None
            if isinstance(self._body, (dict, list)):
                return self._body
            return json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Resp(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub

wf_models = importlib.import_module("models.workflow.model")
Workflow = wf_models.Workflow
WorkflowNode = wf_models.WorkflowNode
WorkflowEdge = wf_models.WorkflowEdge
WorkflowVersion = wf_models.WorkflowVersion
WorkflowNodeType = wf_models.WorkflowNodeType
WorkflowRun = wf_models.WorkflowRun
WorkflowRunStep = wf_models.WorkflowRunStep
WorkflowHumanTask = wf_models.WorkflowHumanTask
WorkflowApproval = wf_models.WorkflowApproval
WorkflowContentBinding = wf_models.WorkflowContentBinding
WorkflowPermission = wf_models.WorkflowPermission
WorkflowFolder = wf_models.WorkflowFolder
WorkflowSchedule = wf_models.WorkflowSchedule
WorkflowAuditLog = wf_models.WorkflowAuditLog
WorkflowPromotion = wf_models.WorkflowPromotion

wf_handler = importlib.import_module("api.workflows.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════
class TestWorkflowModels:
    def test_workflow_from_row(self):
        row = {
            "id": "w1",
            "org_id": "org1",
            "owner_id": "u1",
            "name": "My Flow",
            "description": "desc",
            "status": "draft",
            "environment": "dev",
            "trigger_type": "manual",
            "definition_version": 1,
            "total_runs": 0,
            "success_runs": 0,
            "failed_runs": 0,
            "last_run_at": None,
            "last_run_status": None,
            "is_template": 0,
            "template_category": None,
            "cloned_from": None,
            "tags": "[]",
            "approval_status": "not_required",
            "approval_required": 0,
            "approved_by": None,
            "approved_at": None,
            "approval_note": None,
            "scope_type": "manual",
            "scope_filter": "{}",
            "folder_id": None,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        w = Workflow.from_row(row)
        assert w.id == "w1"
        assert w.name == "My Flow"
        assert w.tags == []
        assert w.scope_filter == {}
        assert w.is_template is False

    def test_workflow_from_row_none(self):
        assert Workflow.from_row(None) is None

    def test_workflow_to_dict_public(self):
        w = Workflow(id="w1", org_id="org1", owner_id="u1", name="F")
        d = w.to_dict()
        assert "id" in d
        assert "approval_status" not in d  # admin only

    def test_workflow_to_dict_admin(self):
        w = Workflow(
            id="w1", org_id="org1", owner_id="u1", name="F", approval_status="approved"
        )
        d = w.to_dict(scope="admin")
        assert d["approval_status"] == "approved"

    def test_workflow_node_from_row(self):
        row = {
            "id": "n1",
            "workflow_id": "w1",
            "node_type_id": "trigger.manual",
            "label": "Start",
            "position_x": 100.0,
            "position_y": 200.0,
            "display_config": '{"color":"blue"}',
            "connector_binding_id": None,
            "created_at": "2026-01-01",
        }
        n = WorkflowNode.from_row(row)
        assert n.label == "Start"
        assert n.display_config == {"color": "blue"}

    def test_workflow_edge_from_row(self):
        row = {
            "id": "e1",
            "workflow_id": "w1",
            "source_node_id": "n1",
            "target_node_id": "n2",
            "condition_label": "yes",
        }
        e = WorkflowEdge.from_row(row)
        assert e.source_node_id == "n1"
        assert e.condition_label == "yes"

    def test_workflow_version_from_row(self):
        row = {
            "id": "v1",
            "workflow_id": "w1",
            "version_number": 3,
            "definition": '{"nodes":[],"edges":[]}',
            "changelog": "Initial",
            "created_by": "u1",
            "created_at": "2026-01-01",
        }
        v = WorkflowVersion.from_row(row)
        assert v.version_number == 3
        assert v.definition == {"nodes": [], "edges": []}

    def test_node_type_from_row(self):
        row = {
            "id": "trigger.manual",
            "category": "trigger",
            "name": "Manual Trigger",
            "description": "Manual",
            "icon": "play",
            "config_schema": "{}",
            "output_schema": "{}",
            "is_enterprise": 0,
            "is_active": 1,
            "connector_definition_id": None,
            "connector_action_id": None,
            "created_at": "2026-01-01",
        }
        nt = WorkflowNodeType.from_row(row)
        assert nt.category == "trigger"
        assert nt.is_enterprise is False

    def test_workflow_run_from_row(self):
        row = {
            "id": "r1",
            "workflow_id": "w1",
            "triggered_by": "manual",
            "trigger_payload": "{}",
            "status": "running",
            "started_at": "2026-01-01",
            "finished_at": None,
            "duration_ms": None,
            "steps_total": 3,
            "steps_succeeded": 0,
            "steps_failed": 0,
            "error_message": None,
            "final_context": "{}",
            "waiting_for_task_id": None,
            "created_at": "2026-01-01",
        }
        r = WorkflowRun.from_row(row)
        assert r.status == "running"
        assert r.steps_total == 3

    def test_human_task_from_row(self):
        row = {
            "id": "t1",
            "run_id": "r1",
            "step_id": "s1",
            "workflow_id": "w1",
            "org_id": "org1",
            "assigned_to": "u2",
            "assigned_role": "EDITOR",
            "assigned_team_id": None,
            "task_title": "Review article",
            "instruction_text": "Please review",
            "input_data": "{}",
            "editable_data": "{}",
            "context_snapshot": "{}",
            "status": "pending",
            "decision": None,
            "reviewer_id": None,
            "reviewer_note": None,
            "output_data": "{}",
            "priority": "high",
            "deadline_at": "2026-02-01",
            "started_review_at": None,
            "completed_at": None,
            "created_at": "2026-01-01",
        }
        t = WorkflowHumanTask.from_row(row)
        assert t.task_title == "Review article"
        assert t.priority == "high"

    def test_approval_from_row(self):
        row = {
            "id": "a1",
            "workflow_id": "w1",
            "version_number": 2,
            "requested_by": "u1",
            "assigned_to": "u2",
            "status": "pending",
            "request_note": "Please approve",
            "review_note": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "expires_at": "2026-03-01",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        a = WorkflowApproval.from_row(row)
        assert a.status == "pending"
        assert a.version_number == 2

    def test_audit_log_from_row(self):
        row = {
            "id": "al1",
            "org_id": "org1",
            "workflow_id": "w1",
            "run_id": "r1",
            "actor_id": "u1",
            "action": "workflow.created",
            "resource_type": "workflow",
            "resource_id": "w1",
            "detail": '{"key":"val"}',
            "ip_hash": "",
            "created_at": "2026-01-01",
        }
        al = WorkflowAuditLog.from_row(row)
        assert al.action == "workflow.created"
        assert al.detail == {"key": "val"}


# ═══════════════════════════════════════════════════════════════
# Fake Service
# ═══════════════════════════════════════════════════════════════
class FakeWorkflowService:
    """Simulates the WorkflowService for handler testing."""

    def __init__(self, env, ctx=None):
        self.calls = []
        self._repo = type(
            "R",
            (),
            {
                "find_workflow": self._find_wf,
            },
        )()

    async def _find_wf(self, wid):
        if wid == "missing":
            return None
        return Workflow(id=wid, org_id="org1", owner_id="u1", name="Test Flow")

    # ── Step 20 ──
    async def list_node_types(self, category=None):
        self.calls.append(("list_node_types", category))
        return [
            {"id": "trigger.manual", "category": "trigger", "name": "Manual"},
            {"id": "action.email", "category": "action", "name": "Send Email"},
        ]

    async def list_workflows(
        self, org_id=None, owner_id=None, status=None, page=1, limit=20
    ):
        self.calls.append(("list_workflows", org_id, owner_id))
        return {
            "workflows": [{"id": "w1", "name": "Test Flow"}],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    async def get_workflow(self, wid):
        self.calls.append(("get_workflow", wid))
        if wid == "missing":
            raise ValueError("Workflow not found")
        return {
            "id": wid,
            "name": "Test Flow",
            "nodes": [],
            "edges": [],
            "org_id": "org1",
            "status": "draft",
        }

    async def create_workflow(self, org_id, owner_id, name, **kwargs):
        self.calls.append(("create_workflow", name))
        if kwargs.get("trigger_type") == "bad":
            raise ValueError("Invalid trigger_type: bad")
        return {"id": "new-w-id"}

    async def update_workflow(self, wid, updated_by, **kwargs):
        self.calls.append(("update_workflow", wid))
        if wid == "missing":
            raise ValueError("Workflow not found")
        return {"id": wid, "name": kwargs.get("name", "Updated")}

    async def delete_workflow(self, wid, deleted_by):
        self.calls.append(("delete_workflow", wid))
        if wid == "missing":
            raise ValueError("Workflow not found")

    async def clone_workflow(self, wid, owner_id, org_id, new_name=None):
        self.calls.append(("clone_workflow", wid))
        if wid == "missing":
            raise ValueError("Source workflow not found")
        return {"id": "cloned-id", "cloned_from": wid}

    async def add_node(self, workflow_id, node_type_id, **kwargs):
        self.calls.append(("add_node", workflow_id, node_type_id))
        if workflow_id == "missing":
            raise ValueError("Workflow not found")
        return {"id": "new-node-id"}

    async def update_node(self, node_id, **kwargs):
        self.calls.append(("update_node", node_id))
        if node_id == "missing":
            raise ValueError("Node not found")
        return {"id": node_id}

    async def delete_node(self, node_id):
        self.calls.append(("delete_node", node_id))
        if node_id == "missing":
            raise ValueError("Node not found")

    async def add_edge(
        self, workflow_id, source_node_id, target_node_id, condition_label=""
    ):
        self.calls.append(("add_edge", workflow_id))
        return {"id": "new-edge-id"}

    async def delete_edge(self, edge_id):
        self.calls.append(("delete_edge", edge_id))
        if edge_id == "missing":
            raise ValueError("Edge not found")

    async def list_versions(self, workflow_id):
        self.calls.append(("list_versions", workflow_id))
        return [{"id": "v1", "version_number": 1}]

    async def create_version(self, workflow_id, created_by, changelog=""):
        self.calls.append(("create_version", workflow_id))
        if workflow_id == "missing":
            raise ValueError("Workflow not found")
        return {"id": "new-ver-id", "version_number": 2}

    async def create_webhook(self, workflow_id, node_id=None, method="POST"):
        self.calls.append(("create_webhook", workflow_id))
        return {"id": "wh1", "token": "secret-token"}

    async def list_webhooks(self, workflow_id):
        self.calls.append(("list_webhooks", workflow_id))
        return [{"id": "wh1", "token": "t"}]

    async def delete_webhook(self, webhook_id):
        self.calls.append(("delete_webhook", webhook_id))

    async def list_templates(self, category=None, page=1, limit=20):
        self.calls.append(("list_templates", category))
        return {"templates": [], "page": page, "limit": limit}

    async def publish_template(
        self,
        workflow_id,
        title,
        short_desc,
        category,
        use_case_tags=None,
        preview_image=None,
    ):
        self.calls.append(("publish_template", workflow_id))
        return {"id": "tpl1"}

    async def clone_from_template(self, template_id, org_id, owner_id):
        self.calls.append(("clone_from_template", template_id))
        return {"id": "cloned-id"}

    async def list_integrations(self, org_id):
        self.calls.append(("list_integrations", org_id))
        return []

    async def create_integration(
        self, org_id, integration_type, name, kv_secret_key, created_by
    ):
        self.calls.append(("create_integration", org_id))
        return {"id": "int1"}

    # ── Step 21 ──
    async def trigger_run(
        self, workflow_id, triggered_by="manual", trigger_payload=None
    ):
        self.calls.append(("trigger_run", workflow_id))
        if workflow_id == "missing":
            raise ValueError("Workflow not found")
        return {
            "id": "run1",
            "workflow_id": workflow_id,
            "status": "running",
            "steps_total": 3,
        }

    async def list_runs(self, workflow_id, page=1, limit=20):
        self.calls.append(("list_runs", workflow_id))
        return {
            "runs": [{"id": "run1", "status": "running"}],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    async def get_run(self, run_id):
        self.calls.append(("get_run", run_id))
        if run_id == "missing":
            raise ValueError("Run not found")
        return {"id": run_id, "status": "running", "steps": []}

    async def cancel_run(self, run_id):
        self.calls.append(("cancel_run", run_id))
        if run_id == "missing":
            raise ValueError("Run not found")
        return {"id": run_id, "status": "cancelled"}

    async def get_run_costs(self, run_id):
        self.calls.append(("get_run_costs", run_id))
        return []

    async def list_messages(self, run_id):
        self.calls.append(("list_messages", run_id))
        return []

    async def add_message(
        self,
        run_id,
        workflow_id,
        sender_id,
        content,
        sender_role="author",
        message_type="comment",
        step_id=None,
        task_id=None,
        attachment_url=None,
        attachment_type=None,
        is_internal=False,
    ):
        self.calls.append(("add_message", run_id))
        return {"id": "msg1"}

    # ── Step 22 ──
    async def list_tasks(self, user_id=None, org_id=None, page=1, limit=20):
        self.calls.append(("list_tasks", user_id))
        return {
            "tasks": [{"id": "t1", "task_title": "Review"}],
            "page": page,
            "limit": limit,
        }

    async def get_task(self, task_id):
        self.calls.append(("get_task", task_id))
        if task_id == "missing":
            raise ValueError("Task not found")
        return {"id": task_id, "task_title": "Review"}

    async def start_task_review(self, task_id, reviewer_id):
        self.calls.append(("start_task_review", task_id))
        if task_id == "missing":
            raise ValueError("Task not found")
        return {"id": task_id, "status": "in_review"}

    async def complete_task(
        self, task_id, reviewer_id, decision, reviewer_note="", output_data=None
    ):
        self.calls.append(("complete_task", task_id, decision))
        if task_id == "missing":
            raise ValueError("Task not found")
        if decision == "bad":
            raise ValueError("Invalid decision: bad")
        return {"id": task_id, "status": "completed", "decision": decision}

    async def list_pending_approvals(self, user_id):
        self.calls.append(("list_pending_approvals", user_id))
        return [{"id": "appr1", "status": "pending"}]

    async def review_approval(self, approval_id, reviewed_by, action, review_note=""):
        self.calls.append(("review_approval", approval_id, action))
        if approval_id == "missing":
            raise ValueError("Approval not found")
        if action == "bad":
            raise ValueError("Invalid action: bad")
        return {"id": approval_id, "status": action}

    async def list_approvals(self, workflow_id):
        self.calls.append(("list_approvals", workflow_id))
        return [{"id": "appr1"}]

    async def request_approval(
        self,
        workflow_id,
        requested_by,
        assigned_to=None,
        request_note="",
        expires_at=None,
    ):
        self.calls.append(("request_approval", workflow_id))
        if workflow_id == "missing":
            raise ValueError("Workflow not found")
        return {"id": "appr-new", "version_number": 1}

    async def list_bindings(self, workflow_id):
        self.calls.append(("list_bindings", workflow_id))
        return []

    async def create_binding(
        self,
        workflow_id,
        org_id,
        bind_type,
        bind_criteria=None,
        trigger_event="on_submit",
        priority=100,
        created_by="",
    ):
        self.calls.append(("create_binding", workflow_id))
        if bind_type == "bad":
            raise ValueError("Invalid bind_type: bad")
        return {"id": "bind1"}

    async def update_binding(self, binding_id, **kwargs):
        self.calls.append(("update_binding", binding_id))
        return {"id": binding_id}

    async def delete_binding(self, binding_id):
        self.calls.append(("delete_binding", binding_id))
        if binding_id == "missing":
            raise ValueError("Binding not found")

    async def list_permissions(self, workflow_id):
        self.calls.append(("list_permissions", workflow_id))
        return []

    async def grant_permission(
        self, workflow_id, grantee_type, grantee_id, permission, granted_by
    ):
        self.calls.append(("grant_permission", workflow_id))
        if grantee_type == "bad":
            raise ValueError("Invalid grantee_type: bad")
        return {"id": "perm1"}

    async def revoke_permission(self, permission_id):
        self.calls.append(("revoke_permission", permission_id))

    async def list_folders(self, org_id):
        self.calls.append(("list_folders", org_id))
        return [{"id": "f1", "name": "My Folder"}]

    async def list_schedules(self, workflow_id=None, org_id=None):
        self.calls.append(("list_schedules", workflow_id))
        return []

    async def create_schedule(
        self,
        org_id,
        workflow_id,
        name,
        cron_expression,
        timezone="UTC",
        next_fire_at=None,
        created_by="",
    ):
        self.calls.append(("create_schedule", workflow_id))
        return {"id": "sch1"}

    async def update_schedule(self, schedule_id, **kwargs):
        self.calls.append(("update_schedule", schedule_id))
        return {"id": schedule_id}

    async def delete_schedule(self, schedule_id):
        self.calls.append(("delete_schedule", schedule_id))
        if schedule_id == "missing":
            raise ValueError("Schedule not found")

    async def get_audit_log(self, workflow_id=None, org_id=None, page=1, limit=50):
        self.calls.append(("get_audit_log", workflow_id))
        return {"audit_log": [], "page": page, "limit": limit}

    async def get_cost_summary(self, workflow_id):
        self.calls.append(("get_cost_summary", workflow_id))
        return {"total_cost_microcents": 0}

    async def list_promotions(self, workflow_id):
        self.calls.append(("list_promotions", workflow_id))
        return []

    async def create_promotion(
        self,
        workflow_id,
        org_id,
        from_env,
        to_env,
        promoted_by,
        approval_id=None,
        promotion_note="",
    ):
        self.calls.append(("create_promotion", workflow_id))
        if from_env == "bad":
            raise ValueError("Invalid environment")
        return {"id": "promo1", "version_number": 1}

    async def handle_webhook_trigger(self, token, payload):
        self.calls.append(("handle_webhook_trigger", token))
        if token == "bad-token":
            raise ValueError("Invalid webhook token")
        return {"id": "run-wh", "workflow_id": "w1", "status": "running"}


# ═══════════════════════════════════════════════════════════════
# Test Helpers
# ═══════════════════════════════════════════════════════════════
class FakeRequest:
    def __init__(self, method, url, headers=None, json_body=None):
        self.method = method
        self.url = f"https://testserver{url}"
        self.headers = headers or {}
        self._json = json_body

    async def json(self):
        return self._json or {}


class FakeCtx:
    trace_id = "test-trace"


class WFClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig_svc = wf_handler.WorkflowService
        wf_handler.WorkflowService = lambda env, ctx=None: self.svc
        try:
            handler_fn = wf_handler.handle_workflows
            if path.startswith("/api/webhooks/"):
                handler_fn = wf_handler.handle_webhook_trigger
            return asyncio.run(
                handler_fn(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            wf_handler.WorkflowService = orig_svc


def _token(sub="u1", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeWorkflowService(_Env())


@pytest.fixture
def client(svc):
    return WFClient(svc)


# ═══════════════════════════════════════════════════════════════
# Step 20 — Core Builder
# ═══════════════════════════════════════════════════════════════
class TestWorkflowCoreHandler:
    def test_list_node_types(self, client, svc):
        resp = client.get(
            "/api/workflow-node-types",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["node_types"]) == 2

    def test_list_workflows(self, client, svc):
        resp = client.get(
            "/api/workflows?org_id=org1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_create_workflow(self, client, svc):
        resp = client.post(
            "/api/workflows",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"org_id": "org1", "name": "My Flow", "trigger_type": "manual"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-w-id"

    def test_create_workflow_bad_trigger(self, client, svc):
        resp = client.post(
            "/api/workflows",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"org_id": "org1", "name": "Bad", "trigger_type": "bad"},
        )
        assert resp.status_code == 400

    def test_get_workflow(self, client, svc):
        resp = client.get(
            "/api/workflows/w1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Flow"

    def test_get_workflow_missing(self, client, svc):
        resp = client.get(
            "/api/workflows/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_update_workflow(self, client, svc):
        resp = client.put(
            "/api/workflows/w1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"name": "Updated Flow"},
        )
        assert resp.status_code == 200

    def test_delete_workflow(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_missing_workflow(self, client, svc):
        resp = client.delete(
            "/api/workflows/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_clone_workflow(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/clone",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"org_id": "org1"},
        )
        assert resp.status_code == 201
        assert resp.json()["cloned_from"] == "w1"

    def test_add_node(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/nodes",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"node_type_id": "trigger.manual", "label": "Start"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-node-id"

    def test_update_node(self, client, svc):
        resp = client.put(
            "/api/workflows/w1/nodes/n1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"label": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_node(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1/nodes/n1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_add_edge(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/edges",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"source_node_id": "n1", "target_node_id": "n2"},
        )
        assert resp.status_code == 201

    def test_delete_edge(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1/edges/e1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_list_versions(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/versions",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["versions"]) == 1

    def test_create_version(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/versions",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"changelog": "v2 changes"},
        )
        assert resp.status_code == 201
        assert resp.json()["version_number"] == 2

    def test_list_webhooks(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/webhooks",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_webhook(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/webhooks",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={},
        )
        assert resp.status_code == 201
        assert "token" in resp.json()

    def test_publish_template(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/publish-template",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={
                "title": "My Template",
                "short_desc": "A template",
                "category": "content",
            },
        )
        assert resp.status_code == 201

    def test_list_templates(self, client, svc):
        resp = client.get(
            "/api/workflow-templates",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_unauthenticated(self, client):
        resp = client.get("/api/workflows")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════
# Step 21 — Execution Engine
# ═══════════════════════════════════════════════════════════════
class TestWorkflowExecutionHandler:
    def test_trigger_run(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/runs",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"triggered_by": "manual"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "running"

    def test_trigger_run_missing_workflow(self, client, svc):
        resp = client.post(
            "/api/workflows/missing/runs",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={},
        )
        assert resp.status_code == 400

    def test_list_runs(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/runs",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_get_run(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/runs/run1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == "run1"

    def test_get_run_missing(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/runs/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_cancel_run(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/runs/run1/cancel",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_get_run_costs(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/runs/run1/costs",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "costs" in resp.json()

    def test_list_run_messages(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/runs/run1/messages",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "messages" in resp.json()

    def test_add_run_message(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/runs/run1/messages",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"content": "Looks good"},
        )
        assert resp.status_code == 201

    def test_webhook_trigger(self, client, svc):
        resp = client.post(
            "/api/webhooks/workflow/valid-token",
            json_body={"event": "push"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "running"

    def test_webhook_invalid_token(self, client, svc):
        resp = client.post(
            "/api/webhooks/workflow/bad-token",
            json_body={},
        )
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════
# Step 22 — HITL + Enterprise
# ═══════════════════════════════════════════════════════════════
class TestWorkflowHITLHandler:
    def test_list_tasks(self, client, svc):
        resp = client.get(
            "/api/workflow-tasks",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["tasks"]) == 1

    def test_get_task(self, client, svc):
        resp = client.get(
            "/api/workflow-tasks/t1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["task_title"] == "Review"

    def test_get_task_missing(self, client, svc):
        resp = client.get(
            "/api/workflow-tasks/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_start_task_review(self, client, svc):
        resp = client.put(
            "/api/workflow-tasks/t1/start",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_review"

    def test_complete_task(self, client, svc):
        resp = client.put(
            "/api/workflow-tasks/t1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"decision": "approved", "reviewer_note": "LGTM"},
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "approved"

    def test_complete_task_bad_decision(self, client, svc):
        resp = client.put(
            "/api/workflow-tasks/t1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"decision": "bad"},
        )
        assert resp.status_code == 400

    def test_list_pending_approvals(self, client, svc):
        resp = client.get(
            "/api/workflow-approvals",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["approvals"]) == 1

    def test_review_approval(self, client, svc):
        resp = client.put(
            "/api/workflow-approvals/appr1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"action": "approved", "review_note": "OK"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_review_approval_bad_action(self, client, svc):
        resp = client.put(
            "/api/workflow-approvals/appr1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"action": "bad"},
        )
        assert resp.status_code == 400


class TestWorkflowEnterpriseHandler:
    def test_list_approvals(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/approvals",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["approvals"]) == 1

    def test_request_approval(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/approvals",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"request_note": "Please review"},
        )
        assert resp.status_code == 201

    def test_list_bindings(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/bindings",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_binding(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/bindings",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"org_id": "org1", "bind_type": "all_org_content"},
        )
        assert resp.status_code == 201

    def test_create_binding_bad_type(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/bindings",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"org_id": "org1", "bind_type": "bad"},
        )
        assert resp.status_code == 400

    def test_update_binding(self, client, svc):
        resp = client.put(
            "/api/workflows/w1/bindings/bind1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"priority": 50},
        )
        assert resp.status_code == 200

    def test_delete_binding(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1/bindings/bind1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_list_permissions(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/permissions",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_grant_permission(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/permissions",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={
                "grantee_type": "user",
                "grantee_id": "u2",
                "permission": "edit",
            },
        )
        assert resp.status_code == 201

    def test_revoke_permission(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1/permissions/perm1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_list_schedules(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/schedules",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_schedule(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/schedules",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={
                "org_id": "org1",
                "name": "Daily",
                "cron_expression": "0 9 * * *",
            },
        )
        assert resp.status_code == 201

    def test_update_schedule(self, client, svc):
        resp = client.put(
            "/api/workflows/w1/schedules/sch1",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={"name": "Updated Schedule"},
        )
        assert resp.status_code == 200

    def test_delete_schedule(self, client, svc):
        resp = client.delete(
            "/api/workflows/w1/schedules/sch1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_get_audit_log(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/audit-log",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "audit_log" in resp.json()

    def test_get_cost_summary(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/costs",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "cost_summary" in resp.json()

    def test_list_promotions(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/promotions",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_promotion(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/promotions",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={
                "org_id": "org1",
                "from_environment": "dev",
                "to_environment": "staging",
            },
        )
        assert resp.status_code == 201

    def test_create_promotion_bad_env(self, client, svc):
        resp = client.post(
            "/api/workflows/w1/promotions",
            headers={"Authorization": f"Bearer {_token()}"},
            json_body={
                "org_id": "org1",
                "from_environment": "bad",
                "to_environment": "staging",
            },
        )
        assert resp.status_code == 400

    def test_list_folders(self, client, svc):
        resp = client.get(
            "/api/workflows/w1/folders",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["folders"]) == 1
