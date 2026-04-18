import types

import pytest

from api.leads import service as leads_service_module
from api.leads.repository import LeadRepository
from api.leads.service import LeadService


class _Env:
    DB = object()


class Obj(types.SimpleNamespace):
    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


class RepoDyn:
    def __init__(self):
        self.responses = {}

    def __getattr__(self, name):
        async def _method(*_args, **_kwargs):
            return self.responses.get(name)

        return _method


@pytest.fixture
def lead_service(monkeypatch):
    svc = LeadService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 80)])
    monkeypatch.setattr(leads_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_lead_service_happy_paths(lead_service):
    svc, repo = lead_service

    repo.responses["list_forms"] = [Obj(id="f1")]
    repo.responses["get_form"] = Obj(
        id="f1",
        name="Form",
        description="",
        placement="inline",
        fields_schema={},
        submit_button_text="Go",
        success_message="ok",
        redirect_url="",
        tags_on_submit=[],
        workflow_id="",
        is_active=True,
    )
    assert (await svc.list_forms("o1"))[0]["id"] == "f1"
    assert (await svc.get_form("f1"))["id"] == "f1"
    assert (await svc.create_form("o1", "u1", "Form", "form"))["id"] == "id-1"
    assert (await svc.update_form("f1", name="Form2"))["id"] == "f1"
    await svc.delete_form("f1")

    repo.responses["list_leads"] = [Obj(id="l1")]
    repo.responses["get_lead"] = Obj(
        id="l1",
        first_name="A",
        last_name="B",
        company="C",
        job_title="J",
        status="new",
        custom_fields={},
    )
    assert (await svc.list_leads("o1"))["leads"][0]["id"] == "l1"
    assert (await svc.get_lead("l1"))["scope"] == "admin"
    assert (await svc.create_lead("o1", "a@b.com"))["id"] == "id-2"
    assert (await svc.create_lead("o1", "a@b.com", capture_form_id="f1"))[
        "id"
    ] == "id-3"
    assert (await svc.update_lead("l1", status="qualified"))["id"] == "l1"
    await svc.delete_lead("l1")

    repo.responses["list_lead_tags"] = ["hot"]
    assert await svc.list_lead_tags("o1", "l1") == ["hot"]
    await svc.add_lead_tag("o1", "l1", "warm")
    await svc.remove_lead_tag("o1", "l1", "warm")

    repo.responses["list_lead_events"] = [Obj(id="ev1")]
    assert (await svc.list_lead_events("l1"))["events"][0]["id"] == "ev1"
    assert (await svc.create_lead_event("l1", "o1", "open"))["id"] == "id-4"

    repo.responses["list_score_rules"] = [Obj(id="r1")]
    repo.responses["get_score_rule"] = Obj(
        id="r1",
        name="N",
        trigger_event="open",
        condition={},
        score_delta=1,
        is_active=True,
    )
    assert (await svc.list_score_rules("o1"))[0]["id"] == "r1"
    assert (await svc.create_score_rule("o1", "N", "open"))["id"] == "id-5"
    assert (await svc.update_score_rule("r1", name="N2"))["id"] == "r1"
    await svc.delete_score_rule("r1")

    repo.responses["list_pipelines"] = [Obj(id="p1")]
    repo.responses["get_pipeline"] = Obj(
        id="p1", name="P", description="", sort_order=1
    )
    assert (await svc.list_pipelines("o1"))[0]["id"] == "p1"
    assert (await svc.get_pipeline("p1"))["id"] == "p1"
    assert (await svc.create_pipeline("o1", "P"))["id"] == "id-6"
    assert (await svc.update_pipeline("p1", name="P2"))["id"] == "p1"
    await svc.delete_pipeline("p1")

    repo.responses["list_stages"] = [Obj(id="s1")]
    repo.responses["get_stage"] = Obj(
        id="s1", name="S", sort_order=1, stage_type="open", color=""
    )
    assert (await svc.list_stages("p1"))[0]["id"] == "s1"
    assert (await svc.create_stage("p1", "S"))["id"] == "id-7"
    assert (await svc.update_stage("s1", name="S2"))["id"] == "s1"
    await svc.delete_stage("s1")

    repo.responses["list_pipeline_entries"] = [Obj(id="pe1")]
    repo.responses["get_pipeline_entry"] = Obj(
        id="pe1", stage_id="s1", assigned_to="u", deal_value=0, notes=""
    )
    assert (await svc.list_pipeline_entries("p1"))["entries"][0]["id"] == "pe1"
    assert (await svc.create_pipeline_entry("l1", "p1", "s1"))["id"] == "id-8"
    assert (await svc.update_pipeline_entry("pe1", notes="n"))["id"] == "pe1"
    await svc.delete_pipeline_entry("pe1")

    repo.responses["list_sequences"] = [Obj(id="seq1")]
    repo.responses["get_sequence"] = Obj(
        id="seq1", name="Seq", description="", trigger_type="signup", status="active"
    )
    assert (await svc.list_sequences("o1"))[0]["id"] == "seq1"
    assert (await svc.get_sequence("seq1"))["id"] == "seq1"
    assert (await svc.create_sequence("o1", "Seq"))["id"] == "id-9"
    assert (await svc.update_sequence("seq1", name="Seq2"))["id"] == "seq1"
    await svc.delete_sequence("seq1")

    repo.responses["list_steps"] = [Obj(id="st1")]
    repo.responses["get_step"] = Obj(
        id="st1", delay_days=1, subject="S", body_html="", body_text=""
    )
    assert (await svc.list_steps("seq1"))[0]["id"] == "st1"
    assert (await svc.create_step("seq1", 1, subject="S"))["id"] == "id-10"
    assert (await svc.update_step("st1", subject="S2"))["id"] == "st1"
    await svc.delete_step("st1")

    repo.responses["list_enrollments"] = [Obj(id="en1")]
    repo.responses["get_enrollment"] = Obj(id="en1", current_step=1, status="active")
    assert (await svc.list_enrollments("seq1"))["enrollments"][0]["id"] == "en1"
    assert (await svc.create_enrollment("l1", "seq1"))["id"] == "id-11"
    assert (await svc.update_enrollment("en1", status="paused"))["id"] == "en1"


@pytest.mark.asyncio
async def test_lead_service_not_found(lead_service):
    svc, repo = lead_service

    repo.responses["get_form"] = None
    with pytest.raises(ValueError, match="Form not found"):
        await svc.get_form("missing")

    repo.responses["get_lead"] = None
    with pytest.raises(ValueError, match="Lead not found"):
        await svc.get_lead("missing")

    repo.responses["get_score_rule"] = None
    with pytest.raises(ValueError, match="Score rule not found"):
        await svc.update_score_rule("missing")

    repo.responses["get_pipeline"] = None
    with pytest.raises(ValueError, match="Pipeline not found"):
        await svc.get_pipeline("missing")

    repo.responses["get_stage"] = None
    with pytest.raises(ValueError, match="Stage not found"):
        await svc.update_stage("missing")

    repo.responses["get_pipeline_entry"] = None
    with pytest.raises(ValueError, match="Pipeline entry not found"):
        await svc.update_pipeline_entry("missing")

    repo.responses["get_sequence"] = None
    with pytest.raises(ValueError, match="Sequence not found"):
        await svc.get_sequence("missing")

    repo.responses["get_step"] = None
    with pytest.raises(ValueError, match="Step not found"):
        await svc.update_step("missing")

    repo.responses["get_enrollment"] = None
    with pytest.raises(ValueError, match="Enrollment not found"):
        await svc.update_enrollment("missing")


@pytest.mark.asyncio
async def test_lead_repository_methods(monkeypatch):
    repo = LeadRepository(db=object())
    execute_calls = []
    find_all_calls = []
    find_one_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        if "lead_tags" in str(sql).lower():
            return [{"tag": "hot"}, {"tag": "warm"}]
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "x"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.list_forms("o1")
    await repo.get_form("f1")
    await repo.create_form(
        "f1", "o1", "u1", "n", "slug", "", "inline", {}, "Go", "ok", "", [], "", True
    )
    await repo.update_form("f1", "n", "", "inline", {}, "Go", "ok", "", [], "", True)
    await repo.delete_form("f1")
    await repo.inc_form_submissions("f1")
    await repo.list_leads("o1", None, 20, 0)
    await repo.list_leads("o1", "new", 20, 0)
    await repo.get_lead("l1")
    await repo.get_lead_by_email("o1", "a@b.com")
    await repo.create_lead(
        "l1",
        "o1",
        "a@b.com",
        "A",
        "B",
        "C",
        "J",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        {},
        False,
        False,
        "",
        "",
        "",
    )
    await repo.update_lead("l1", "A", "B", "C", "J", "new", {})
    await repo.update_lead_score("l1", 5)
    await repo.delete_lead("l1")
    assert await repo.list_lead_tags("o1", "l1") == ["hot", "warm"]
    await repo.add_lead_tag("o1", "l1", "hot")
    await repo.remove_lead_tag("o1", "l1", "hot")
    await repo.list_lead_events("l1", 50, 0)
    await repo.create_lead_event("ev1", "l1", "o1", "open", {}, "u1")
    await repo.list_score_rules("o1")
    await repo.get_score_rule("r1")
    await repo.create_score_rule("r1", "o1", "n", "open", {}, 1, True)
    await repo.update_score_rule("r1", "n", "open", {}, 1, False)
    await repo.delete_score_rule("r1")
    await repo.list_pipelines("o1")
    await repo.get_pipeline("p1")
    await repo.create_pipeline("p1", "o1", "n", "", 1)
    await repo.update_pipeline("p1", "n", "", 1)
    await repo.delete_pipeline("p1")
    await repo.list_stages("p1")
    await repo.get_stage("s1")
    await repo.create_stage("s1", "p1", "n", 1, "open", "")
    await repo.update_stage("s1", "n", 1, "open", "")
    await repo.delete_stage("s1")
    await repo.list_pipeline_entries("p1", 50, 0)
    await repo.get_pipeline_entry("pe1")
    await repo.create_pipeline_entry("pe1", "l1", "p1", "s1", "", 0, "")
    await repo.update_pipeline_entry("pe1", "s1", "", 0, "")
    await repo.delete_pipeline_entry("pe1")
    await repo.list_sequences("o1")
    await repo.get_sequence("seq1")
    await repo.create_sequence("seq1", "o1", "n", "", "trigger", "u1")
    await repo.update_sequence("seq1", "n", "", "trigger", "active")
    await repo.delete_sequence("seq1")
    await repo.list_steps("seq1")
    await repo.get_step("st1")
    await repo.create_step("st1", "seq1", 1, 0, "sub", "", "")
    await repo.update_step("st1", 1, "sub", "", "")
    await repo.delete_step("st1")
    await repo.list_enrollments("seq1", 50, 0)
    await repo.get_enrollment("en1")
    await repo.create_enrollment("en1", "l1", "seq1")
    await repo.update_enrollment("en1", 2, "paused")

    assert len(execute_calls) == 31
    assert len(find_all_calls) == 12
    assert len(find_one_calls) == 10
