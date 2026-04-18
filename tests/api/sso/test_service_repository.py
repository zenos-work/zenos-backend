import types

import pytest

from api.sso import service as sso_service_module
from api.sso.repository import SsoRepository
from api.sso.service import SsoService


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
def sso_service(monkeypatch):
    svc = SsoService(_Env())
    repo = RepoDyn()
    svc._repo = repo
    seq = iter([f"id-{i}" for i in range(1, 50)])
    monkeypatch.setattr(sso_service_module, "new_id", lambda: next(seq))
    return svc, repo


@pytest.mark.asyncio
async def test_sso_service_happy_paths(sso_service):
    svc, repo = sso_service

    repo.responses["list_configs"] = [Obj(id="c1")]
    repo.responses["get_config"] = Obj(id="c1")
    assert (await svc.list_configs("o1"))[0]["id"] == "c1"
    assert (await svc.get_config("c1"))["id"] == "c1"

    repo.responses["create_config"] = None
    created_obj = Obj(
        id="id-1",
        org_id="o1",
        provider_type="okta",
        protocol="oidc",
        client_id="cid",
        client_secret="sec",
        issuer_url="https://issuer",
        metadata_url="",
        entity_id="",
        acs_url="https://acs",
        slo_url="",
        certificate="",
        is_active=True,
        enforce_sso=False,
        jit_provisioning=True,
        default_role="READER",
        allowed_domains="",
    )
    repo.responses["get_active_config"] = created_obj
    cfg = await svc.create_config(
        "o1",
        {
            "provider_type": "okta",
            "protocol": "oidc",
            "issuer_url": "https://issuer",
            "client_id": "cid",
            "acs_url": "https://acs",
        },
    )
    assert cfg["provider_type"] == "okta"

    repo.responses["get_config"] = Obj(
        id="c1",
        provider_type="okta",
        protocol="oidc",
        client_id="",
        client_secret="",
        issuer_url="https://issuer",
        metadata_url="",
        entity_id="",
        acs_url="",
        slo_url="",
        certificate="",
        is_active=True,
        enforce_sso=False,
        jit_provisioning=True,
        default_role="READER",
        allowed_domains="",
    )
    updated = await svc.update_config("c1", {"client_id": "new"})
    assert updated["client_id"] == "new"

    deleted = await svc.delete_config("c1")
    assert deleted["deleted"] is True

    repo.responses["get_active_config"] = Obj(
        protocol="oidc",
        issuer_url="https://issuer",
        client_id="cid",
        acs_url="https://acs",
    )
    authz = await svc.oidc_authorize_url("o1", "https://r")
    assert "authorize_url" in authz

    repo.responses["get_session_by_state"] = Obj(
        id="sid", org_id="o1", redirect_url="https://r"
    )
    cb = await svc.oidc_callback("o1", authz["state"], "code")
    assert cb["status"] == "authenticated"

    repo.responses["get_active_config"] = Obj(
        protocol="saml", issuer_url="https://idp", entity_id="", acs_url=""
    )
    md = await svc.saml_metadata("o1")
    assert "EntityDescriptor" in md
    sl = await svc.saml_login_url("o1")
    assert "login_url" in sl
    repo.responses["get_session_by_state"] = Obj(id="sid", org_id="o1")
    acs = await svc.saml_acs("o1", "resp", sl["state"])
    assert acs["assertion_received"] is True


@pytest.mark.asyncio
async def test_sso_service_validation_errors(sso_service):
    svc, repo = sso_service
    with pytest.raises(ValueError, match="provider_type"):
        await svc.create_config("o1", {"protocol": "oidc"})
    with pytest.raises(ValueError, match="issuer_url"):
        await svc.create_config("o1", {"provider_type": "okta", "protocol": "oidc"})
    repo.responses["get_config"] = None
    with pytest.raises(ValueError, match="SSO config not found"):
        await svc.update_config("x", {})
    repo.responses["get_active_config"] = None
    with pytest.raises(ValueError, match="No active OIDC"):
        await svc.oidc_authorize_url("o1")
    repo.responses["get_session_by_state"] = None
    with pytest.raises(ValueError, match="Invalid or expired SSO state"):
        await svc.oidc_callback("o1", "bad", "c")
    repo.responses["get_active_config"] = None
    with pytest.raises(ValueError, match="No active SAML"):
        await svc.saml_metadata("o1")


@pytest.mark.asyncio
async def test_sso_repository_methods(monkeypatch):
    repo = SsoRepository(db=object())
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

    cfg = Obj(
        id="c1",
        org_id="o1",
        provider_type="okta",
        protocol="oidc",
        client_id="",
        client_secret="",
        issuer_url="",
        metadata_url="",
        entity_id="",
        acs_url="",
        slo_url="",
        certificate="",
        is_active=True,
        enforce_sso=False,
        jit_provisioning=True,
        default_role="READER",
        allowed_domains="",
    )
    await repo.get_config("c1")
    await repo.get_active_config("o1")
    await repo.list_configs("o1")
    await repo.create_config(cfg)
    await repo.update_config(cfg)
    await repo.delete_config("c1")
    await repo.deactivate_config("c1")
    await repo.create_session("s1", "o1", "st", "nonce", "https://r")
    await repo.get_session_by_state("st")
    await repo.delete_session("s1")
    await repo.cleanup_expired()

    assert len(execute_calls) > 6
