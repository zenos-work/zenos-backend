import types

import pytest

from api.org_infra import service as org_infra_service_module
from api.org_infra.repository import OrgInfraRepository
from api.org_infra.service import OrgInfraService


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
def infra_service(monkeypatch):
    svc = OrgInfraService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 50)])
    monkeypatch.setattr(org_infra_service_module, "new_id", lambda: next(seq))
    monkeypatch.setattr(
        org_infra_service_module.secrets, "token_urlsafe", lambda _n: "tokenvalue123456"
    )
    return svc, repo


@pytest.mark.asyncio
async def test_org_infra_service_happy_paths(infra_service):
    svc, repo = infra_service

    aid = await svc.log_action("o1", "u1", "create")
    assert aid == "id-1"

    repo.responses["find_audit_by_org"] = [Obj(id="a1")]
    repo.responses["count_audit_by_org"] = 1
    audit = await svc.list_audit_log("o1")
    assert audit["audit_log"][0]["scope"] == "admin"

    created = await svc.create_api_key("o1", "Key", "read", "u1")
    assert created["key_prefix"]

    repo.responses["find_api_keys"] = [Obj(id="k1")]
    repo.responses["count_api_keys"] = 1
    keys = await svc.list_api_keys("o1")
    assert keys["api_keys"][0]["id"] == "k1"

    await svc.revoke_api_key("k1", "o1")

    sso_calls = {"count": 0}

    async def _find_sso_by_org(_org_id):
        sso_calls["count"] += 1
        if sso_calls["count"] == 1:
            return None
        return Obj(id="sso1", provider="saml")

    repo.find_sso_by_org = _find_sso_by_org
    created_sso = await svc.create_sso("o1", "saml", "{}", True, "u1")
    assert created_sso["id"] == "sso1"

    repo.responses["find_sso_by_org"] = Obj(id="sso1", provider="oidc")
    updated_sso = await svc.update_sso("o1", "oidc", "{}", True)
    assert updated_sso["id"] == "sso1"
    got_sso = await svc.get_sso("o1")
    assert got_sso["id"] == "sso1"


@pytest.mark.asyncio
async def test_org_infra_service_validation_errors(infra_service):
    svc, repo = infra_service

    with pytest.raises(ValueError, match="Invalid provider"):
        await svc.create_sso("o1", "bad", "{}", True, "u1")

    repo.responses["find_sso_by_org"] = Obj(id="s1")
    with pytest.raises(ValueError, match="already exists"):
        await svc.create_sso("o1", "saml", "{}", True, "u1")

    with pytest.raises(ValueError, match="Invalid provider"):
        await svc.update_sso("o1", "bad", "{}", True)

    repo.responses["find_sso_by_org"] = None
    with pytest.raises(ValueError, match="No SSO config"):
        await svc.update_sso("o1", "saml", "{}", True)

    with pytest.raises(ValueError, match="No SSO config"):
        await svc.get_sso("o1")


@pytest.mark.asyncio
async def test_org_infra_repository_methods(monkeypatch):
    repo = OrgInfraRepository(db=object())
    execute_calls = []

    async def _execute(sql, *params):
        execute_calls.append((sql, params))

    async def _find_all(sql, *params):
        return [{"id": "x"}, {"id": "y"}]

    async def _find_one(sql, *params):
        return {"id": "x", "c": 2}

    monkeypatch.setattr(repo, "execute", _execute)
    monkeypatch.setattr(repo, "find_all", _find_all)
    monkeypatch.setattr(repo, "find_one", _find_one)
    monkeypatch.setattr(repo, "map_many", lambda rows, _model: rows)
    monkeypatch.setattr(repo, "map_one", lambda row, _model: row)

    await repo.insert_audit("a1", "o1", "u1", "ip", "act", "res", "rid", "{}")
    await repo.find_audit_by_org("o1", 20, 0)
    assert await repo.count_audit_by_org("o1") == 2
    await repo.create_api_key("k1", "o1", "N", "hash", "pref", "read", "u1")
    await repo.find_api_keys("o1", 20, 0)
    assert await repo.count_api_keys("o1") == 2
    await repo.revoke_api_key("k1", "o1")
    await repo.create_sso("s1", "o1", "saml", "{}", True, "u1")
    await repo.find_sso_by_org("o1")
    await repo.update_sso("o1", "oidc", "{}", True)

    assert len(execute_calls) >= 5
