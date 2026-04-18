import types

import pytest

from api.connectors import service as connectors_service_module
from api.connectors.repository import ConnectorRepository
from api.connectors.service import ConnectorService


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
def connector_service(monkeypatch):
    svc = ConnectorService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 80)])
    monkeypatch.setattr(connectors_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_connector_service_happy_paths(connector_service):
    svc, repo = connector_service

    repo.responses["list_definitions"] = [Obj(id="d1")]
    repo.responses["get_definition"] = Obj(id="d1")
    repo.responses["get_definition_by_slug"] = Obj(id="d2")
    repo.responses["list_actions"] = [Obj(id="a1")]
    assert (await svc.list_definitions())[0]["id"] == "d1"
    assert (await svc.get_definition("d1"))["scope"] == "admin"
    assert (await svc.get_definition_by_slug("slug"))["scope"] == "admin"
    assert (await svc.list_actions("d1"))[0]["id"] == "a1"

    repo.responses["list_instances"] = [Obj(id="i1")]
    repo.responses["get_instance"] = Obj(
        id="i1", name="I", instance_config={}, status="pending_auth"
    )
    assert (await svc.list_instances("o1"))[0]["id"] == "i1"
    assert (await svc.get_instance("i1"))["scope"] == "admin"
    assert (await svc.create_instance("o1", "d1", "Name"))["id"] == "id-1"
    assert (await svc.update_instance("i1", name="N2"))["id"] == "i1"
    await svc.delete_instance("i1")

    repo.responses["list_mcp_servers"] = [Obj(id="m1")]
    repo.responses["get_mcp_server"] = Obj(
        id="m1", name="M", description="", endpoint_url="", status="pending"
    )
    assert (await svc.list_mcp_servers("o1"))[0]["id"] == "m1"
    assert (await svc.get_mcp_server("m1"))["id"] == "m1"
    assert (await svc.create_mcp_server("o1", "M"))["id"] == "id-2"
    assert (await svc.update_mcp_server("m1", name="M2"))["id"] == "m1"
    await svc.delete_mcp_server("m1")

    repo.responses["list_agents"] = [Obj(id="ag1")]
    repo.responses["get_agent"] = Obj(
        id="ag1",
        name="A",
        description="",
        model_config_data={},
        system_prompt="",
        is_active=True,
    )
    assert (await svc.list_agents("o1"))[0]["id"] == "ag1"
    assert (await svc.get_agent("ag1"))["id"] == "ag1"
    assert (await svc.create_agent("o1", "A"))["id"] == "id-3"
    assert (await svc.update_agent("ag1", name="A2"))["id"] == "ag1"
    await svc.delete_agent("ag1")

    repo.responses["list_marketplace"] = [Obj(id="l1")]
    repo.responses["get_marketplace_listing"] = Obj(id="l1")
    assert (await svc.list_marketplace())[0]["id"] == "l1"
    assert (await svc.get_marketplace_listing("l1"))["id"] == "l1"
    assert (await svc.publish_listing("d1", "o1", "u1", "Title", "Short"))[
        "id"
    ] == "id-4"

    repo.responses["list_installs"] = [{"id": "ins1"}]
    assert (await svc.list_installs("o1"))[0]["id"] == "ins1"
    await svc.install_connector("o1", "d1", "u1")
    await svc.uninstall_connector("o1", "d1")

    repo.responses["get_node_binding"] = {"id": "b1"}
    assert (await svc.get_node_binding("node1"))["id"] == "b1"
    assert (await svc.create_node_binding("node1", "i1", "a1"))["id"] == "id-5"
    await svc.delete_node_binding("b1")


@pytest.mark.asyncio
async def test_connector_service_not_found(connector_service):
    svc, repo = connector_service
    repo.responses["get_definition"] = None
    with pytest.raises(ValueError, match="definition"):
        await svc.get_definition("x")
    repo.responses["get_definition_by_slug"] = None
    with pytest.raises(ValueError, match="definition"):
        await svc.get_definition_by_slug("x")
    repo.responses["get_instance"] = None
    with pytest.raises(ValueError, match="instance"):
        await svc.get_instance("x")
    repo.responses["get_mcp_server"] = None
    with pytest.raises(ValueError, match="MCP server"):
        await svc.get_mcp_server("x")
    repo.responses["get_agent"] = None
    with pytest.raises(ValueError, match="Custom agent"):
        await svc.get_agent("x")
    repo.responses["get_marketplace_listing"] = None
    with pytest.raises(ValueError, match="Marketplace listing"):
        await svc.get_marketplace_listing("x")


@pytest.mark.asyncio
async def test_connector_repository_methods(monkeypatch):
    repo = ConnectorRepository(db=object())
    execute_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        return {"id": "x"}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.list_definitions()
    await repo.list_definitions("cat")
    await repo.get_definition("d1")
    await repo.get_definition_by_slug("slug")
    await repo.list_actions("d1")
    await repo.get_action("a1")
    await repo.list_instances("o1")
    await repo.get_instance("i1")
    await repo.create_instance(
        "i1", "o1", "d1", "N", "none", None, {}, "pending_auth", "u1"
    )
    await repo.update_instance("i1", "N", {}, "active")
    await repo.delete_instance("i1")
    await repo.list_mcp_servers("o1")
    await repo.get_mcp_server("m1")
    await repo.create_mcp_server(
        "m1", "o1", "N", "", "sse", None, None, [], "bearer", None, [], "pending", "u1"
    )
    await repo.update_mcp_server("m1", "N", "", "", "active")
    await repo.delete_mcp_server("m1")
    await repo.list_agents("o1")
    await repo.get_agent("ag1")
    await repo.create_agent(
        "ag1", "o1", "N", "", "llm", "cf", "mid", {}, "", [], None, None, True, "u1"
    )
    await repo.update_agent("ag1", "N", "", {}, "", True)
    await repo.delete_agent("ag1")
    await repo.list_marketplace()
    await repo.get_marketplace_listing("l1")
    await repo.create_marketplace_listing(
        "l1", "d1", "o1", "u1", "T", "S", "", [], True
    )
    await repo.list_installs("o1")
    await repo.install_connector("o1", "d1", "u1")
    await repo.uninstall_connector("o1", "d1")
    assert await repo.get_node_binding("node1") == {"id": "x"}
    await repo.create_node_binding("b1", "node1", "i1", "a1", {}, {}, 2, 30, 120)
    await repo.delete_node_binding("b1")

    assert len(execute_calls) >= 14
