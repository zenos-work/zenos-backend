import types

import pytest

from api.workflows.service import WorkflowService
from api.workflows import service as workflow_service_module


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class DynRepo:
    def __init__(self):
        self.responses = {}
        self.calls = []

    def __getattr__(self, name):
        async def _method(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            value = self.responses.get(name)
            if callable(value):
                return value(*args, **kwargs)
            return value

        return _method


@pytest.fixture
def workflow_service(monkeypatch):
    service = WorkflowService(_Env())
    repo = DynRepo()
    service._repo = repo
    monkeypatch.setattr(
        workflow_service_module,
        "new_id",
        lambda: f"id-{len(repo.calls) + 1}",
    )
    monkeypatch.setattr(
        workflow_service_module.secrets, "token_urlsafe", lambda _n: "tok"
    )
    return service, repo


@pytest.mark.asyncio
async def test_list_and_read_workflows(workflow_service):
    service, repo = workflow_service
    repo.responses["find_workflows_by_org_status"] = [Obj(id="w1")]
    repo.responses["count_workflows_by_org"] = 7
    result = await service.list_workflows(
        org_id="org1", status="active", page=2, limit=5
    )
    assert result["total"] == 7
    assert result["workflows"][0]["id"] == "w1"

    repo.responses["find_workflows_by_owner"] = [Obj(id="w2")]
    repo.responses["count_workflows_by_owner"] = 2
    owner_result = await service.list_workflows(owner_id="u1")
    assert owner_result["workflows"][0]["id"] == "w2"

    none_result = await service.list_workflows()
    assert none_result["workflows"] == []

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.get_workflow("missing")

    repo.responses["find_workflow"] = Obj(id="wf1", name="WF")
    repo.responses["get_nodes"] = [Obj(id="n1")]
    repo.responses["get_edges"] = [Obj(id="e1")]
    wf = await service.get_workflow("wf1")
    assert wf["id"] == "wf1"
    assert wf["nodes"][0]["id"] == "n1"
    assert wf["edges"][0]["id"] == "e1"


@pytest.mark.asyncio
async def test_create_update_delete_and_clone_workflow(workflow_service):
    service, repo = workflow_service

    with pytest.raises(ValueError, match="Invalid trigger_type"):
        await service.create_workflow("o", "u", "name", trigger_type="bad")
    with pytest.raises(ValueError, match="Invalid environment"):
        await service.create_workflow("o", "u", "name", environment="bad")
    with pytest.raises(ValueError, match="Invalid scope_type"):
        await service.create_workflow("o", "u", "name", scope_type="bad")

    created = await service.create_workflow(
        "org1",
        "owner1",
        "Workflow Name",
        tags=["t1"],
        scope_filter={"a": 1},
        approval_required=True,
    )
    assert created["id"].startswith("id-")

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.update_workflow("missing", updated_by="u")

    repo.responses["find_workflow"] = Obj(
        id="wf1",
        org_id="org1",
        name="Old",
        description="Desc",
        status="draft",
        environment="dev",
        trigger_type="manual",
        tags=["x"],
        scope_type="manual",
        scope_filter={"k": "v"},
        folder_id=None,
        approval_required=False,
    )
    with pytest.raises(ValueError, match="Invalid status"):
        await service.update_workflow("wf1", updated_by="u", status="bad")
    with pytest.raises(ValueError, match="Invalid environment"):
        await service.update_workflow("wf1", updated_by="u", environment="bad")
    with pytest.raises(ValueError, match="Invalid trigger_type"):
        await service.update_workflow("wf1", updated_by="u", trigger_type="bad")

    updated = await service.update_workflow(
        "wf1",
        updated_by="u1",
        name="New",
        tags=["n"],
        scope_filter={"only": True},
    )
    assert updated["id"] == "wf1"

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.delete_workflow("missing", "u")

    repo.responses["find_workflow"] = Obj(id="wf1", org_id="org1")
    await service.delete_workflow("wf1", "u")

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Source workflow not found"):
        await service.clone_workflow("missing", "u", "org1")

    repo.responses["find_workflow"] = Obj(
        id="wf1",
        name="Base",
        description="d",
        environment="dev",
        trigger_type="manual",
        tags=["x"],
        scope_type="manual",
        scope_filter={"k": "v"},
        folder_id=None,
        approval_required=False,
    )
    repo.responses["get_nodes"] = [
        Obj(
            id="old-n1",
            node_type_id="t1",
            label="N1",
            position_x=1,
            position_y=2,
            display_config={"a": 1},
            connector_binding_id=None,
        )
    ]
    repo.responses["get_edges"] = [
        Obj(source_node_id="old-n1", target_node_id="old-n1", condition_label="ok")
    ]
    cloned = await service.clone_workflow("wf1", "u1", "org1", new_name="copy")
    assert cloned["cloned_from"] == "wf1"


@pytest.mark.asyncio
async def test_nodes_edges_versions_webhooks_templates_integrations(workflow_service):
    service, repo = workflow_service

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.add_node("wf", "nt")

    repo.responses["find_workflow"] = Obj(id="wf")
    repo.responses["get_node_type"] = None
    with pytest.raises(ValueError, match="Invalid node_type_id"):
        await service.add_node("wf", "bad")

    repo.responses["get_node_type"] = Obj(id="nt")
    added_node = await service.add_node("wf", "nt", display_config={"x": 1})
    assert added_node["id"].startswith("id-")

    repo.responses["get_node"] = None
    with pytest.raises(ValueError, match="Node not found"):
        await service.update_node("missing")

    repo.responses["get_node"] = Obj(
        id="n1",
        label="L",
        position_x=1,
        position_y=2,
        display_config={"a": 1},
        connector_binding_id=None,
    )
    updated_node = await service.update_node("n1", label="L2")
    assert updated_node["id"] == "n1"

    repo.responses["get_node"] = None
    with pytest.raises(ValueError, match="Node not found"):
        await service.delete_node("n-missing")

    repo.responses["get_node"] = Obj(id="n1")
    await service.delete_node("n1")

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.add_edge("missing", "n1", "n2")

    repo.responses["find_workflow"] = Obj(id="wf")
    edge = await service.add_edge("wf", "n1", "n2", "yes")
    assert edge["id"].startswith("id-")

    repo.responses["get_edge"] = None
    with pytest.raises(ValueError, match="Edge not found"):
        await service.delete_edge("e1")

    repo.responses["get_edge"] = Obj(id="e1")
    await service.delete_edge("e1")

    repo.responses["find_workflow"] = Obj(
        id="wf",
        name="WF",
        description="D",
        status="draft",
        environment="dev",
        trigger_type="manual",
        tags=[],
        scope_type="manual",
        scope_filter={},
        folder_id=None,
        approval_required=False,
    )
    repo.responses["get_latest_version"] = Obj(version_number=2)
    repo.responses["get_nodes"] = [Obj(id="n1")]
    repo.responses["get_edges"] = [Obj(id="e1")]
    version = await service.create_version("wf", "u1", changelog="c")
    assert version["version_number"] == 3

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.create_webhook("missing")

    repo.responses["find_workflow"] = Obj(id="wf")
    webhook = await service.create_webhook("wf")
    assert webhook["token"] == "tok"

    repo.responses["get_webhook"] = None
    with pytest.raises(ValueError, match="Webhook not found"):
        await service.delete_webhook("missing")

    repo.responses["get_webhook"] = Obj(id="wh1")
    await service.delete_webhook("wh1")

    repo.responses["get_templates_by_category"] = [Obj(id="t1")]
    categorized = await service.list_templates(category="growth")
    assert categorized["templates"][0]["id"] == "t1"

    repo.responses["get_templates"] = [Obj(id="t2")]
    all_templates = await service.list_templates()
    assert all_templates["templates"][0]["id"] == "t2"

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.publish_template("missing", "T", "S", "cat")

    repo.responses["find_workflow"] = Obj(id="wf")
    published = await service.publish_template("wf", "T", "S", "cat", ["a"])
    assert published["id"].startswith("id-")

    repo.responses["get_template"] = None
    with pytest.raises(ValueError, match="Template not found"):
        await service.clone_from_template("missing", "org1", "u1")

    repo.responses["find_workflow"] = Obj(
        id="wf",
        name="WF",
        description="D",
        environment="dev",
        trigger_type="manual",
        tags=[],
        scope_type="manual",
        scope_filter={},
        folder_id=None,
        approval_required=False,
    )
    repo.responses["get_nodes"] = []
    repo.responses["get_edges"] = []
    repo.responses["get_template"] = Obj(workflow_id="wf")
    cloned = await service.clone_from_template("tpl1", "org1", "u1")
    assert cloned["cloned_from"] == "wf"

    repo.responses["get_integrations"] = [Obj(id="i1")]
    ints = await service.list_integrations("org1")
    assert ints[0]["id"] == "i1"
    created_int = await service.create_integration("org1", "slack", "Slack", "k", "u1")
    assert created_int["id"].startswith("id-")

    repo.responses["get_integration"] = None
    with pytest.raises(ValueError, match="Integration not found"):
        await service.delete_integration("missing")
    repo.responses["get_integration"] = Obj(id="i1")
    await service.delete_integration("i1")


@pytest.mark.asyncio
async def test_runs_tasks_approvals_bindings_permissions_and_misc(workflow_service):
    service, repo = workflow_service

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.trigger_run("missing")

    repo.responses["find_workflow"] = Obj(id="wf", org_id="org1", status="draft")
    with pytest.raises(ValueError, match="must be active"):
        await service.trigger_run("wf")

    repo.responses["find_workflow"] = Obj(id="wf", org_id="org1", status="active")
    repo.responses["get_nodes"] = [
        Obj(id="n1", node_type_id="t1"),
        Obj(id="n2", node_type_id="t2"),
    ]
    run = await service.trigger_run(
        "wf", triggered_by="manual", trigger_payload={"x": 1}
    )
    assert run["status"] == "running"
    assert run["steps_total"] == 2

    repo.responses["get_webhook_by_token"] = None
    with pytest.raises(ValueError, match="Invalid webhook token"):
        await service.handle_webhook_trigger("bad", {})

    repo.responses["get_webhook_by_token"] = Obj(id="wh", workflow_id="wf")
    hook_run = await service.handle_webhook_trigger("good", {"k": "v"})
    assert hook_run["workflow_id"] == "wf"

    repo.responses["get_runs"] = [Obj(id="r1")]
    repo.responses["count_runs"] = 1
    runs = await service.list_runs("wf")
    assert runs["runs"][0]["id"] == "r1"

    repo.responses["get_run"] = None
    with pytest.raises(ValueError, match="Run not found"):
        await service.get_run("missing")

    repo.responses["get_run"] = Obj(id="r1", workflow_id="wf", status="running")
    repo.responses["get_run_steps"] = [Obj(id="s1")]
    run_info = await service.get_run("r1")
    assert run_info["steps"][0]["id"] == "s1"

    repo.responses["get_run"] = None
    with pytest.raises(ValueError, match="Run not found"):
        await service.cancel_run("missing")

    repo.responses["get_run"] = Obj(id="r1", workflow_id="wf", status="completed")
    with pytest.raises(ValueError, match="Only running workflows"):
        await service.cancel_run("r1")

    repo.responses["get_run"] = Obj(id="r1", workflow_id="wf", status="running")
    cancelled = await service.cancel_run("r1")
    assert cancelled["status"] == "cancelled"

    repo.responses["get_tasks_for_user"] = [Obj(id="t1")]
    user_tasks = await service.list_tasks(user_id="u1")
    assert user_tasks["tasks"][0]["id"] == "t1"

    repo.responses["get_tasks_for_org"] = [Obj(id="t2")]
    org_tasks = await service.list_tasks(org_id="org1")
    assert org_tasks["tasks"][0]["id"] == "t2"

    repo.responses["get_task"] = None
    with pytest.raises(ValueError, match="Task not found"):
        await service.get_task("missing")

    repo.responses["get_task"] = Obj(
        id="t1", status="pending", org_id="org1", workflow_id="wf", run_id="r1"
    )
    task = await service.get_task("t1")
    assert task["id"] == "t1"

    repo.responses["get_task"] = Obj(
        id="t1", status="in_review", org_id="org1", workflow_id="wf", run_id="r1"
    )
    with pytest.raises(ValueError, match="not pending"):
        await service.start_task_review("t1", "u")

    repo.responses["get_task"] = Obj(
        id="t1", status="pending", org_id="org1", workflow_id="wf", run_id="r1"
    )
    reviewed = await service.start_task_review("t1", "u")
    assert reviewed["id"] == "t1"

    repo.responses["get_task"] = Obj(
        id="t1", status="done", org_id="org1", workflow_id="wf", run_id="r1"
    )
    with pytest.raises(ValueError, match="cannot be completed"):
        await service.complete_task("t1", "u", "approved")

    repo.responses["get_task"] = Obj(
        id="t1", status="pending", org_id="org1", workflow_id="wf", run_id="r1"
    )
    with pytest.raises(ValueError, match="Invalid decision"):
        await service.complete_task("t1", "u", "bad")

    completed = await service.complete_task(
        "t1", "u", "approved", output_data={"ok": True}
    )
    assert completed["status"] == "completed"

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.request_approval("missing", "u")

    repo.responses["find_workflow"] = Obj(id="wf", org_id="org1", definition_version=3)
    repo.responses["get_latest_version"] = None
    approval = await service.request_approval("wf", "u")
    assert approval["version_number"] == 3

    repo.responses["get_approval"] = None
    with pytest.raises(ValueError, match="Approval not found"):
        await service.review_approval("missing", "u", "approved")

    repo.responses["get_approval"] = Obj(id="a1", workflow_id="wf", status="done")
    with pytest.raises(ValueError, match="not pending"):
        await service.review_approval("a1", "u", "approved")

    repo.responses["get_approval"] = Obj(id="a1", workflow_id="wf", status="pending")
    with pytest.raises(ValueError, match="Invalid action"):
        await service.review_approval("a1", "u", "bad")

    reviewed_approval = await service.review_approval("a1", "u", "approved")
    assert reviewed_approval["status"] == "approved"

    repo.responses["get_approvals"] = [Obj(id="a1")]
    repo.responses["get_pending_approvals_for_user"] = [Obj(id="a2")]
    assert (await service.list_approvals("wf"))[0]["id"] == "a1"
    assert (await service.list_pending_approvals("u"))[0]["id"] == "a2"

    with pytest.raises(ValueError, match="Invalid bind_type"):
        await service.create_binding("wf", "org1", "bad")
    with pytest.raises(ValueError, match="Invalid trigger_event"):
        await service.create_binding(
            "wf", "org1", "all_org_content", trigger_event="bad"
        )

    binding = await service.create_binding("wf", "org1", "all_org_content")
    assert binding["id"].startswith("id-")

    repo.responses["get_binding"] = None
    with pytest.raises(ValueError, match="Binding not found"):
        await service.update_binding("missing")

    repo.responses["get_binding"] = Obj(
        id="b1",
        bind_type="all_org_content",
        bind_criteria={},
        trigger_event="on_submit",
        priority=1,
        is_active=True,
    )
    with pytest.raises(ValueError, match="Invalid bind_type"):
        await service.update_binding("b1", bind_type="bad")
    with pytest.raises(ValueError, match="Invalid trigger_event"):
        await service.update_binding("b1", trigger_event="bad")
    assert (await service.update_binding("b1"))["id"] == "b1"

    repo.responses["get_binding"] = None
    with pytest.raises(ValueError, match="Binding not found"):
        await service.delete_binding("missing")
    repo.responses["get_binding"] = Obj(id="b1")
    await service.delete_binding("b1")

    with pytest.raises(ValueError, match="Invalid grantee_type"):
        await service.grant_permission("wf", "bad", "u", "view", "admin")
    with pytest.raises(ValueError, match="Invalid permission"):
        await service.grant_permission("wf", "user", "u", "bad", "admin")

    grant = await service.grant_permission("wf", "user", "u", "view", "admin")
    assert grant["id"].startswith("id-")
    await service.revoke_permission("perm1")

    repo.responses["get_messages"] = [Obj(id="m1")]
    assert (await service.list_messages("run1"))[0]["id"] == "m1"
    message = await service.add_message("run1", "wf", "u1", "hello")
    assert message["id"].startswith("id-")

    repo.responses["get_policies"] = [Obj(id="p1")]
    assert (await service.list_policies("org1"))[0]["id"] == "p1"
    created_policy = await service.create_policy(
        "org1", "rate_limit", {"r": 1}, created_by="u1"
    )
    assert created_policy["id"].startswith("id-")

    repo.responses["get_policy"] = None
    with pytest.raises(ValueError, match="Policy not found"):
        await service.update_policy("missing")
    repo.responses["get_policy"] = Obj(id="p1", policy_value={"r": 1}, is_active=True)
    assert (await service.update_policy("p1", {"r": 2}, False))["id"] == "p1"

    repo.responses["get_folders"] = [Obj(id="f1")]
    assert (await service.list_folders("org1"))[0]["id"] == "f1"
    created_folder = await service.create_folder("org1", "Folder")
    assert created_folder["id"].startswith("id-")

    repo.responses["get_folder"] = None
    with pytest.raises(ValueError, match="Folder not found"):
        await service.update_folder("missing")
    repo.responses["get_folder"] = Obj(
        id="f1",
        name="Folder",
        description="",
        icon="",
        sort_order=0,
        parent_id=None,
    )
    assert (await service.update_folder("f1", name="Renamed"))["id"] == "f1"

    repo.responses["get_folder"] = None
    with pytest.raises(ValueError, match="Folder not found"):
        await service.delete_folder("missing")
    repo.responses["get_folder"] = Obj(id="f1")
    await service.delete_folder("f1")

    repo.responses["get_schedules_by_workflow"] = [Obj(id="s1")]
    assert (await service.list_schedules(workflow_id="wf"))[0]["id"] == "s1"
    repo.responses["get_schedules_by_org"] = [Obj(id="s2")]
    assert (await service.list_schedules(org_id="org1"))[0]["id"] == "s2"
    assert await service.list_schedules() == []

    created_schedule = await service.create_schedule("org1", "wf", "daily", "0 0 * * *")
    assert created_schedule["id"].startswith("id-")

    repo.responses["get_schedule"] = None
    with pytest.raises(ValueError, match="Schedule not found"):
        await service.update_schedule("missing")
    repo.responses["get_schedule"] = Obj(
        id="s1",
        name="daily",
        cron_expression="0 0 * * *",
        timezone="UTC",
        is_active=True,
        next_fire_at=None,
    )
    assert (await service.update_schedule("s1", timezone="Asia/Kolkata"))["id"] == "s1"

    repo.responses["get_schedule"] = None
    with pytest.raises(ValueError, match="Schedule not found"):
        await service.delete_schedule("missing")
    repo.responses["get_schedule"] = Obj(id="s1")
    await service.delete_schedule("s1")

    repo.responses["get_audit_by_workflow"] = [Obj(id="a1")]
    repo.responses["get_audit_by_org"] = [Obj(id="a2")]
    assert (await service.get_audit_log(workflow_id="wf"))["audit_log"][0]["id"] == "a1"
    assert (await service.get_audit_log(org_id="org1"))["audit_log"][0]["id"] == "a2"
    assert (await service.get_audit_log())["audit_log"] == []

    repo.responses["get_costs_by_run"] = [Obj(id="c1")]
    repo.responses["get_cost_summary"] = None
    assert (await service.get_run_costs("r1"))[0]["id"] == "c1"
    assert await service.get_cost_summary("wf") == {}

    repo.responses["get_promotions"] = [Obj(id="pr1")]
    assert (await service.list_promotions("wf"))[0]["id"] == "pr1"
    with pytest.raises(ValueError, match="Invalid environment"):
        await service.create_promotion("wf", "org1", "bad", "dev", "u")

    repo.responses["find_workflow"] = None
    with pytest.raises(ValueError, match="Workflow not found"):
        await service.create_promotion("wf", "org1", "dev", "staging", "u")

    repo.responses["find_workflow"] = Obj(id="wf", definition_version=1)
    repo.responses["get_latest_version"] = Obj(version_number=4)
    promo = await service.create_promotion("wf", "org1", "dev", "staging", "u")
    assert promo["version_number"] == 4


@pytest.mark.asyncio
async def test_list_node_types_and_audit_failure_is_swallowed(workflow_service):
    service, repo = workflow_service
    repo.responses["get_node_types"] = [Obj(id="nt1")]
    assert (await service.list_node_types())[0]["id"] == "nt1"

    repo.responses["get_node_types_by_category"] = [Obj(id="nt2")]
    assert (await service.list_node_types("genai"))[0]["id"] == "nt2"

    def _raise(*_args, **_kwargs):
        raise RuntimeError("audit down")

    repo.responses["log_audit"] = _raise
    await service._audit("org1", "wf1", None, "u", "workflow.updated")
