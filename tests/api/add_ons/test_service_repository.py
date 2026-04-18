import pytest

from api.add_ons.repository import AddOnRepository
from api.add_ons.service import AddOnService


class _Env:
    DB = object()


class AddOnObj:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self, scope=None):
        data = dict(self.__dict__)
        if scope is not None:
            data["scope"] = scope
        return data


@pytest.mark.asyncio
async def test_add_on_service_enable_update_disable_and_get_usage(monkeypatch):
    service = AddOnService(_Env())
    monkeypatch.setattr("api.add_ons.service.new_id", lambda: "ao-new")

    state = {
        "addon": None,
        "created": None,
        "updated": None,
        "disabled": None,
    }

    async def _find_by_org_type(org_id, add_on_type):
        return state["addon"]

    async def _create(aid, org_id, add_on_type, tier, enabled_by, limits):
        state["created"] = (aid, org_id, add_on_type, tier, enabled_by, limits)
        state["addon"] = AddOnObj(
            id=aid,
            org_id=org_id,
            add_on_type=add_on_type,
            tier=tier,
            enabled_by=enabled_by,
            limits=limits,
            is_active=1,
        )

    async def _update(org_id, add_on_type, tier, limits):
        state["updated"] = (org_id, add_on_type, tier, limits)
        state["addon"].tier = tier
        state["addon"].limits = limits

    async def _disable(org_id, add_on_type):
        state["disabled"] = (org_id, add_on_type)

    async def _find_by_org(_org_id):
        return [state["addon"]] if state["addon"] else []

    async def _summary():
        return [{"add_on_type": "workflow_builder", "count": 3}]

    monkeypatch.setattr(service._repo, "find_by_org_type", _find_by_org_type)
    monkeypatch.setattr(service._repo, "create_add_on", _create)
    monkeypatch.setattr(service._repo, "update_add_on", _update)
    monkeypatch.setattr(service._repo, "disable_add_on", _disable)
    monkeypatch.setattr(service._repo, "find_by_org", _find_by_org)
    monkeypatch.setattr(service._repo, "summary", _summary)

    with pytest.raises(ValueError, match="Invalid add-on type"):
        await service.enable_add_on("org1", "bad_type", "pro", "admin")

    state["addon"] = AddOnObj(add_on_type="workflow_builder", is_active=1)
    with pytest.raises(ValueError, match="already active"):
        await service.enable_add_on("org1", "workflow_builder", "pro", "admin")

    state["addon"] = None
    enabled = await service.enable_add_on("org1", "workflow_builder", "pro", "admin")
    assert enabled["id"] == "ao-new"
    assert state["created"][2] == "workflow_builder"

    state["addon"] = None
    with pytest.raises(ValueError, match="Add-on not found"):
        await service.update_add_on("org1", "workflow_builder", "unlimited")

    state["addon"] = AddOnObj(
        id="ao-1",
        add_on_type="workflow_builder",
        tier="pro",
        limits="{}",
        is_active=1,
    )
    updated = await service.update_add_on(
        "org1", "workflow_builder", "unlimited", '{"max":10}'
    )
    assert updated["tier"] == "unlimited"
    assert state["updated"][2] == "unlimited"

    state["addon"] = None
    with pytest.raises(ValueError, match="Add-on not found"):
        await service.disable_add_on("org1", "workflow_builder")

    state["addon"] = AddOnObj(add_on_type="workflow_builder", is_active=1)
    await service.disable_add_on("org1", "workflow_builder")
    assert state["disabled"] == ("org1", "workflow_builder")

    state["addon"] = AddOnObj(
        id="ao-2",
        add_on_type="workflow_builder",
        tier="pro",
        limits='{"max": 5}',
        is_active=1,
    )
    listed = await service.list_add_ons("org1")
    assert listed["add_ons"][0]["add_on_type"] == "workflow_builder"

    usage = await service.get_usage("org1", "workflow_builder")
    assert usage["is_active"] == 1

    state["addon"] = None
    with pytest.raises(ValueError, match="Add-on not found"):
        await service.get_usage("org1", "workflow_builder")

    summary = await service.summary()
    assert summary["summary"][0]["count"] == 3


@pytest.mark.asyncio
async def test_add_on_repository_methods(monkeypatch):
    repo = AddOnRepository(db=object())

    execute_calls = []
    find_all_calls = []
    find_one_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        find_all_calls.append((sql, params))
        if len(find_all_calls) == 1:
            return [{"id": "a1"}, {"id": "a2"}]
        return [{"add_on_type": "workflow_builder", "c": 2}]

    async def _find_one(sql, *params):
        find_one_calls.append((sql, params))
        return {"id": "a1"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.create_add_on("a1", "org1", "workflow_builder", "pro", "u1", "{}")
    found = await repo.find_by_org("org1")
    assert found[0]["id"] == "a1"

    found_one = await repo.find_by_org_type("org1", "workflow_builder")
    assert found_one["id"] == "a1"

    await repo.update_add_on("org1", "workflow_builder", "unlimited", '{"x":1}')
    await repo.disable_add_on("org1", "workflow_builder")

    summary = await repo.summary()
    assert summary == [{"add_on_type": "workflow_builder", "count": 2}]

    assert len(execute_calls) == 3
    assert len(find_all_calls) == 2
    assert len(find_one_calls) == 1
