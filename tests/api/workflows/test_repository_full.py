import pytest

from api.workflows.repository import WorkflowRepository


@pytest.mark.asyncio
async def test_workflow_repository_methods(monkeypatch):
    repo = WorkflowRepository(db=object())
    execute_calls = []

    async def _execute(sql, params=None):
        execute_calls.append((sql, params))

    async def _find_one(sql, params=None):
        return {"cnt": 2, "id": "x"}

    async def _one(_model, _sql, _params=None):
        return {"id": "x"}

    async def _many(_model, _sql, _params=None):
        return [{"id": "x"}, {"id": "y"}]

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "_one", _one)
    monkeypatch.setattr(repo, "_many", _many)

    await repo.get_node_types()
    await repo.get_node_types_by_category("genai")
    await repo.get_node_type("nt1")
    await repo.find_workflows_by_org("o1", 20, 0)
    await repo.find_workflows_by_owner("u1", 20, 0)
    await repo.find_workflows_by_org_status("o1", "active", 20, 0)
    await repo.find_workflow("w1")
    assert await repo.count_workflows_by_org("o1") == 2
    assert await repo.count_workflows_by_owner("u1") == 2
    await repo.create_workflow(
        "w1",
        "o1",
        "u1",
        "N",
        "D",
        "draft",
        "dev",
        "manual",
        "[]",
        "manual",
        "{}",
        None,
        False,
    )
    await repo.update_workflow(
        "w1", "N", "D", "active", "dev", "manual", "[]", "manual", "{}", None, True
    )
    await repo.delete_workflow("w1")
    await repo.update_workflow_status("w1", "active")
    await repo.update_run_stats("w1", "success")
    await repo.get_nodes("w1")
    await repo.get_node("n1")
    await repo.create_node("n1", "w1", "nt1", "L", 0, 0, "{}", None)
    await repo.update_node("n1", "L", 1, 2, "{}", None)
    await repo.delete_node("n1")
    await repo.get_edges("w1")
    await repo.get_edge("e1")
    await repo.create_edge("e1", "w1", "n1", "n2", "")
    await repo.delete_edge("e1")
    await repo.get_versions("w1")
    await repo.get_version("v1")
    await repo.get_latest_version("w1")
    await repo.create_version("v1", "w1", 1, "{}", "", "u1")
    await repo.get_webhooks("w1")
    await repo.get_webhook_by_token("tok")
    await repo.get_webhook("wh1")
    await repo.create_webhook("wh1", "w1", "n1", "tok", "POST")
    await repo.record_webhook_hit("wh1")
    await repo.delete_webhook("wh1")
    await repo.get_templates(20, 0)
    await repo.get_templates_by_category("ops", 20, 0)
    await repo.get_template("t1")
    await repo.create_template("t1", "w1", "T", "S", "ops", "[]", "")
    await repo.increment_template_download("t1")
    await repo.get_integrations("o1")
    await repo.get_integration("i1")
    await repo.create_integration("i1", "o1", "slack", "Slack", "k", "u1")
    await repo.delete_integration("i1")
    await repo.get_runs("w1", 20, 0)
    await repo.get_run("r1")
    assert await repo.count_runs("w1") == 2
    await repo.create_run("r1", "w1", "u1", "{}", 3)
    await repo.finish_run("r1", "success", 100, "", 3, 0, "{}")
    await repo.cancel_run("r1")
    await repo.set_run_waiting("r1", "t1")
    await repo.get_run_steps("r1")
    await repo.get_run_step("s1")
    await repo.create_run_step("s1", "r1", "n1", "nt1", 1, "{}")
    await repo.update_run_step("s1", "success", "{}", "", 10)
    await repo.get_tasks_for_user("u1", 20, 0)
    await repo.get_tasks_for_org("o1", 20, 0)
    await repo.get_task("t1")
    await repo.create_task(
        "t1",
        "r1",
        "s1",
        "w1",
        "o1",
        "u1",
        "admin",
        "team",
        "title",
        "instr",
        "{}",
        "{}",
        "{}",
        1,
        "",
    )
    await repo.complete_task("t1", "approved", "approve", "u1", "ok", "{}")
    await repo.start_task_review("t1", "u1")
    await repo.get_approvals("w1")
    await repo.get_approval("a1")
    await repo.get_pending_approvals_for_user("u1")
    await repo.create_approval("a1", "w1", 1, "u1", "u2", "", "")
    await repo.review_approval("a1", "approved", "ok", "u2")
    await repo.get_bindings_by_workflow("w1")
    await repo.get_bindings_by_org("o1")
    await repo.get_binding("b1")
    await repo.create_binding("b1", "w1", "o1", "article", "{}", "publish", 1, "u1")
    await repo.update_binding("b1", "article", "{}", "publish", 1, True)
    await repo.delete_binding("b1")
    await repo.get_permissions("w1")
    await repo.get_permissions_for_user("w1", "u1", "admin")
    await repo.create_permission("p1", "w1", "user", "u1", "edit", "u1")
    await repo.delete_permission("p1")
    await repo.get_messages("r1")
    await repo.create_message(
        "m1", "r1", "w1", "s1", "t1", "u1", "admin", "hi", "note", "", "", False
    )
    await repo.get_policies("o1")
    await repo.get_policy("pl1")
    await repo.create_policy("pl1", "o1", "cost", "{}", "system", "u1")
    await repo.update_policy("pl1", "{}", True)
    await repo.get_folders("o1")
    await repo.get_folder("f1")
    await repo.create_folder("f1", "o1", None, "Folder", "", "", 1, "u1")
    await repo.update_folder("f1", "Folder", "", "", 1, None)
    await repo.delete_folder("f1")
    await repo.get_schedules_by_workflow("w1")
    await repo.get_schedules_by_org("o1")
    await repo.get_schedule("sc1")
    await repo.get_due_schedules()
    await repo.create_schedule("sc1", "o1", "w1", "Sched", "* * * * *", "UTC", "", "u1")
    await repo.update_schedule("sc1", "Sched", "* * * * *", "UTC", True, "")
    await repo.record_schedule_fired("sc1", "")
    await repo.delete_schedule("sc1")
    await repo.get_audit_by_workflow("w1", 20, 0)
    await repo.get_audit_by_org("o1", 20, 0)
    await repo.log_audit("a1", "o1", "w1", "r1", "u1", "act", "res", "rid", "{}", "ip")
    await repo.get_costs_by_run("r1")
    await repo.get_costs_by_workflow("w1", 20, 0)
    await repo.create_run_cost(
        "c1",
        "r1",
        "s1",
        "w1",
        "o1",
        "nt1",
        "tokens",
        10,
        "tok",
        100,
        120,
        "USD",
        "ext",
        "",
    )
    assert isinstance(await repo.get_cost_summary("w1"), dict)
    await repo.get_promotions("w1")
    await repo.create_promotion("pr1", "w1", "o1", "dev", "staging", 1, "u1", None, "")
    await repo.update_promotion_status("pr1", "promoted")

    assert len(execute_calls) >= 48
