"""Tests for Phase 11 — Enterprise Infrastructure & Tenant Isolation.

Covers:
- Step 41: Subdomain provisioning + tenant routing
- Step 42: SAML/OIDC SSO handler
- Step 43: Tenant-scoped query middleware (RLS)
- Step 44: Credential vault API
- Step 45: Cache-header strategy
"""

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

# ── Imports under test ───────────────────────────────────────
sub_models = importlib.import_module("models.subdomain.model")
SubdomainConfig = sub_models.SubdomainConfig
OrgContext = sub_models.OrgContext

sso_models = importlib.import_module("models.sso.model")
SsoConfig = sso_models.SsoConfig
SsoSession = sso_models.SsoSession

vault_models = importlib.import_module("models.vault.model")
VaultSecret = vault_models.VaultSecret
VaultWriteQuota = vault_models.VaultWriteQuota

sub_handler = importlib.import_module("api.subdomains.handler")
sso_handler = importlib.import_module("api.sso.handler")
vault_handler = importlib.import_module("api.vault.handler")

tenant_router = importlib.import_module("middleware.tenant_router")
rls = importlib.import_module("middleware.rls")
cache_headers = importlib.import_module("middleware.cache_headers")

create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════
class TestEnterpriseInfraModels:
    def test_subdomain_config_from_row_and_to_dict(self):
        row = {
            "org_id": "org1",
            "subdomain": "acme",
            "is_active": 1,
            "provisioned_by": "u1",
            "ssl_status": "active",
            "settings": "{}",
        }
        m = SubdomainConfig.from_row(row)
        assert m.org_id == "org1"
        assert m.is_active is True
        d = m.to_dict(scope="admin")
        assert d["subdomain"] == "acme"
        assert d["provisioned_by"] == "u1"

    def test_org_context_from_row(self):
        row = {"id": "org1", "subdomain": "acme", "plan": "enterprise", "is_active": 1}
        o = OrgContext.from_row(row)
        assert o.org_id == "org1"
        assert o.plan == "enterprise"

    def test_sso_config_from_row(self):
        row = {
            "id": "cfg1",
            "org_id": "org1",
            "provider_type": "okta",
            "protocol": "oidc",
            "issuer_url": "https://idp.example.com",
            "is_active": 1,
            "jit_provisioning": 1,
        }
        c = SsoConfig.from_row(row)
        assert c.id == "cfg1"
        assert c.protocol == "oidc"
        assert c.is_active is True

    def test_sso_session_from_row(self):
        row = {"id": "s1", "org_id": "org1", "state": "st1", "nonce": "n1"}
        s = SsoSession.from_row(row)
        assert s.state == "st1"

    def test_vault_secret_from_row(self):
        row = {
            "id": "sec1",
            "org_id": "org1",
            "name": "stripe_key",
            "secret_type": "api_key",
            "is_active": 1,
        }
        s = VaultSecret.from_row(row)
        assert s.name == "stripe_key"
        assert s.is_active is True

    def test_vault_quota_from_row(self):
        row = {
            "org_id": "org1",
            "date": "2026-04-10",
            "write_count": 7,
            "max_writes": 50,
        }
        q = VaultWriteQuota.from_row(row)
        assert q.write_count == 7
        assert q.to_dict()["remaining"] == 43


# ═══════════════════════════════════════════════════════════════
# Middleware Tests
# ═══════════════════════════════════════════════════════════════
class _Req:
    def __init__(self, host=""):
        self.headers = {"Host": host}


class _FakeOrgCtx:
    def __init__(self):
        self.is_active = True

    def to_dict(self):
        return {
            "org_id": "org1",
            "subdomain": "acme",
            "plan": "enterprise",
            "is_active": True,
        }


class _FakeSubRepo:
    def __init__(self, *_args, **_kwargs):
        pass

    async def resolve_org(self, subdomain):
        if subdomain == "acme":
            return _FakeOrgCtx()
        return None


class TestTenantRouterMiddleware:
    def test_resolve_tenant_success(self, monkeypatch):
        monkeypatch.setattr(tenant_router, "SubdomainRepository", _FakeSubRepo)

        class _Env:
            DB = object()

        out = asyncio.run(tenant_router.resolve_tenant(_Req("acme.zenos.com"), _Env()))
        assert out["org_id"] == "org1"

    def test_resolve_tenant_reserved_subdomain(self, monkeypatch):
        monkeypatch.setattr(tenant_router, "SubdomainRepository", _FakeSubRepo)

        class _Env:
            DB = object()

        out = asyncio.run(tenant_router.resolve_tenant(_Req("www.zenos.com"), _Env()))
        assert out is None


class TestRlsMiddleware:
    def test_scoped_query_adds_where(self):
        ctx = rls.RlsContext("org1", "AUTHOR")
        sql, params = ctx.scoped_query("SELECT * FROM articles", [])
        assert "WHERE org_id = ?" in sql
        assert params[-1] == "org1"

    def test_scoped_query_adds_and(self):
        ctx = rls.RlsContext("org1", "AUTHOR")
        sql, params = ctx.scoped_query(
            "SELECT * FROM articles WHERE status = ?", ["PUBLISHED"]
        )
        assert "AND org_id = ?" in sql
        assert params == ["PUBLISHED", "org1"]

    def test_superadmin_bypass(self):
        ctx = rls.RlsContext("org1", "SUPERADMIN")
        sql, params = ctx.scoped_query("SELECT * FROM articles", [])
        assert sql == "SELECT * FROM articles"
        assert params == []

    def test_enforce_cross_tenant_denied(self):
        ctx = rls.RlsContext("org1", "AUTHOR")
        with pytest.raises(PermissionError):
            ctx.enforce("org2")

    def test_resolve_rls_from_header(self):
        class R:
            headers = {"X-Org-Id": "orgh"}

        out = rls.resolve_rls({"role": "AUTHOR"}, R())
        assert out.org_id == "orgh"


class TestCacheHeaderMiddleware:
    def test_public_article_cache(self):
        cc = cache_headers.cache_control_for_request(
            "/api/articles/test", "GET", "zenos.com"
        )
        assert "public" in cc
        assert "s-maxage=3600" in cc

    def test_enterprise_subdomain_private(self):
        cc = cache_headers.cache_control_for_request(
            "/api/feed", "GET", "acme.zenos.com"
        )
        assert "private" in cc
        assert "no-store" in cc

    def test_mutating_no_store(self):
        cc = cache_headers.cache_control_for_request(
            "/api/articles/x", "POST", "zenos.com"
        )
        assert cc == "no-store"

    def test_apply_cache_headers_sets_header(self):
        resp = type("R", (), {"headers": {}})()
        out = cache_headers.apply_cache_headers(resp, "/api/feed", "GET", "zenos.com")
        assert out.headers["Cache-Control"].startswith("public")


# ═══════════════════════════════════════════════════════════════
# Handler Test Infrastructure
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


def _token(sub="u1", role="AUTHOR", org_id="org1"):
    return create_token({"sub": sub, "role": role, "org_id": org_id}, _JWT_SECRET)


def _make_client(handler_mod, handler_func_name, service_class_name, fake_svc):
    handler_func = getattr(handler_mod, handler_func_name)

    class Client:
        def __init__(self, svc_instance):
            self.svc = svc_instance

        def _dispatch(self, method, path, headers=None, json_body=None):
            parsed = urlparse(path)
            req = FakeRequest(
                method=method, url=path, headers=headers or {}, json_body=json_body
            )

            class _Env:
                JWT_SECRET = _JWT_SECRET
                DB = object()

            orig = getattr(handler_mod, service_class_name)
            setattr(handler_mod, service_class_name, lambda env, ctx=None: self.svc)
            try:
                return asyncio.run(
                    handler_func(
                        req,
                        _Env(),
                        parsed.path,
                        method,
                        parse_qs(parsed.query),
                        FakeCtx(),
                    )
                )
            finally:
                setattr(handler_mod, service_class_name, orig)

        def get(self, path, headers=None):
            return self._dispatch("GET", path, headers=headers)

        def post(self, path, headers=None, json_body=None):
            return self._dispatch("POST", path, headers=headers, json_body=json_body)

        def put(self, path, headers=None, json_body=None):
            return self._dispatch("PUT", path, headers=headers, json_body=json_body)

        def delete(self, path, headers=None, json_body=None):
            return self._dispatch("DELETE", path, headers=headers, json_body=json_body)

    return Client(fake_svc)


# ═══════════════════════════════════════════════════════════════
# Fake Services for Handler Tests
# ═══════════════════════════════════════════════════════════════
class FakeSubdomainService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def org_info(self, subdomain):
        self.calls.append(("org_info", subdomain))
        if subdomain == "missing":
            return None
        return {"org_id": "org1", "subdomain": subdomain, "name": "Acme"}

    async def provision(self, org_id, subdomain, provisioned_by, custom_domain=""):
        self.calls.append(("provision", org_id, subdomain))
        if subdomain == "taken":
            raise ValueError("already taken")
        return {"org_id": org_id, "subdomain": subdomain, "status": "provisioned"}

    async def update(self, org_id, subdomain):
        self.calls.append(("update", org_id, subdomain))
        if subdomain == "bad":
            raise ValueError("invalid")
        return {"org_id": org_id, "subdomain": subdomain, "status": "updated"}

    async def get_by_org(self, org_id):
        self.calls.append(("get_by_org", org_id))
        if org_id == "missing":
            return None
        return {"org_id": org_id, "subdomain": "acme"}

    async def list_all(self, limit=50, offset=0):
        self.calls.append(("list_all", limit, offset))
        return [{"org_id": "org1", "subdomain": "acme"}]

    async def deactivate(self, org_id):
        self.calls.append(("deactivate", org_id))
        return {"org_id": org_id, "status": "deactivated"}

    async def delete(self, org_id):
        self.calls.append(("delete", org_id))
        return {"org_id": org_id, "status": "deleted"}


class FakeSsoService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def saml_metadata(self, org_id):
        self.calls.append(("saml_metadata", org_id))
        if org_id == "missing":
            raise ValueError("missing")
        return "<xml>metadata</xml>"

    async def saml_login_url(self, org_id):
        self.calls.append(("saml_login_url", org_id))
        if org_id == "missing":
            raise ValueError("missing")
        return {"login_url": "https://idp/login", "state": "st1"}

    async def saml_acs(self, org_id, saml_response, relay_state):
        self.calls.append(("saml_acs", org_id))
        if relay_state == "bad":
            raise ValueError("invalid")
        return {"org_id": org_id, "status": "authenticated"}

    async def oidc_authorize_url(self, org_id, redirect_url=""):
        self.calls.append(("oidc_authorize_url", org_id, redirect_url))
        if org_id == "missing":
            raise ValueError("missing")
        return {"authorize_url": "https://idp/authorize", "state": "st1"}

    async def oidc_callback(self, org_id, state, code):
        self.calls.append(("oidc_callback", org_id, state, code))
        if state == "bad":
            raise ValueError("invalid")
        return {"org_id": org_id, "status": "authenticated"}

    async def list_configs(self, org_id):
        self.calls.append(("list_configs", org_id))
        return [{"id": "cfg1", "org_id": org_id}]

    async def create_config(self, org_id, data):
        self.calls.append(("create_config", org_id))
        if not data.get("provider_type"):
            raise ValueError("provider_type required")
        return {"id": "cfg1", "org_id": org_id}

    async def update_config(self, config_id, data):
        self.calls.append(("update_config", config_id))
        if config_id == "missing":
            raise ValueError("not found")
        return {"id": config_id}

    async def delete_config(self, config_id):
        self.calls.append(("delete_config", config_id))
        return {"id": config_id, "deleted": True}


class FakeVaultService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def store_secret(self, org_id, name, secret_type, created_by, metadata="{}"):
        self.calls.append(("store_secret", org_id, name))
        if not name:
            raise ValueError("name required")
        if name == "quota-hit":
            raise PermissionError("quota")
        return {"id": "sec1", "name": name, "secret_type": secret_type}

    async def list_secrets(self, org_id):
        self.calls.append(("list_secrets", org_id))
        return [{"id": "sec1", "name": "stripe_key"}]

    async def revoke_secret(self, org_id, secret_id):
        self.calls.append(("revoke_secret", org_id, secret_id))
        if secret_id == "missing":
            raise ValueError("not found")
        return {"id": secret_id, "revoked": True}

    async def rotate_secret(self, org_id, name):
        self.calls.append(("rotate_secret", org_id, name))
        if name == "missing":
            raise ValueError("not found")
        if name == "quota-hit":
            raise PermissionError("quota")
        return {"name": name, "rotated": True}

    async def test_secret(self, org_id, name):
        self.calls.append(("test_secret", org_id, name))
        if name == "missing":
            raise ValueError("not found")
        return {"name": name, "exists": True}


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════
@pytest.fixture
def sub_client():
    return _make_client(
        sub_handler, "handle_subdomains", "SubdomainService", FakeSubdomainService(None)
    )


@pytest.fixture
def sso_client():
    return _make_client(sso_handler, "handle_sso", "SsoService", FakeSsoService(None))


@pytest.fixture
def vault_client():
    return _make_client(
        vault_handler, "handle_vault", "VaultService", FakeVaultService(None)
    )


# ═══════════════════════════════════════════════════════════════
# Subdomain Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestSubdomainHandler:
    def _auth(self, role="SUPERADMIN"):
        return {"Authorization": f"Bearer {_token(role=role)}"}

    def test_well_known_org_info_success(self, sub_client):
        resp = sub_client.get("/.well-known/org-info?subdomain=acme")
        assert resp.status_code == 200
        assert resp.json()["org_id"] == "org1"

    def test_well_known_org_info_missing(self, sub_client):
        resp = sub_client.get("/.well-known/org-info?subdomain=missing")
        assert resp.status_code == 404

    def test_admin_provision_subdomain(self, sub_client):
        resp = sub_client.post(
            "/api/admin/organizations/org1/subdomain",
            headers=self._auth("SUPERADMIN"),
            json_body={"subdomain": "acme"},
        )
        assert resp.status_code == 201

    def test_admin_provision_forbidden(self, sub_client):
        resp = sub_client.post(
            "/api/admin/organizations/org1/subdomain",
            headers=self._auth("AUTHOR"),
            json_body={"subdomain": "acme"},
        )
        assert resp.status_code == 403

    def test_org_update_subdomain(self, sub_client):
        resp = sub_client.put(
            "/api/organizations/org1/subdomain",
            headers=self._auth("AUTHOR"),
            json_body={"subdomain": "acme-updated"},
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# SSO Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestSsoHandler:
    def _auth(self):
        return {"Authorization": f"Bearer {_token(role='SUPERADMIN')}"}

    def test_saml_metadata(self, sso_client):
        resp = sso_client.get("/api/auth/sso/saml/org1/metadata")
        assert resp.status_code == 200
        assert "metadata" in resp.json()

    def test_saml_login(self, sso_client):
        resp = sso_client.get("/api/auth/sso/saml/org1/login")
        assert resp.status_code == 200
        assert "login_url" in resp.json()

    def test_saml_acs_invalid_state(self, sso_client):
        resp = sso_client.post(
            "/api/auth/sso/saml/org1/acs",
            json_body={"SAMLResponse": "x", "RelayState": "bad"},
        )
        assert resp.status_code == 400

    def test_oidc_authorize(self, sso_client):
        resp = sso_client.get("/api/auth/sso/oidc/org1/authorize?redirect_url=/app")
        assert resp.status_code == 200
        assert "authorize_url" in resp.json()

    def test_oidc_callback(self, sso_client):
        resp = sso_client.get("/api/auth/sso/oidc/org1/callback?state=ok&code=abc")
        assert resp.status_code == 200
        assert resp.json()["status"] == "authenticated"

    def test_sso_config_requires_auth(self, sso_client):
        resp = sso_client.get("/api/organizations/org1/sso/configs")
        assert resp.status_code == 401

    def test_sso_config_create(self, sso_client):
        resp = sso_client.post(
            "/api/organizations/org1/sso/configs",
            headers=self._auth(),
            json_body={
                "provider_type": "okta",
                "protocol": "oidc",
                "issuer_url": "https://idp",
            },
        )
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════
# Vault Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestVaultHandler:
    def _auth(self):
        return {"Authorization": f"Bearer {_token(role='SUPERADMIN')}"}

    def test_store_secret(self, vault_client):
        resp = vault_client.post(
            "/api/organizations/org1/vault/secrets",
            headers=self._auth(),
            json_body={"name": "stripe_key", "secret_type": "api_key"},
        )
        assert resp.status_code == 201

    def test_store_secret_quota_hit(self, vault_client):
        resp = vault_client.post(
            "/api/organizations/org1/vault/secrets",
            headers=self._auth(),
            json_body={"name": "quota-hit", "secret_type": "api_key"},
        )
        assert resp.status_code == 429

    def test_list_secrets(self, vault_client):
        resp = vault_client.get(
            "/api/organizations/org1/vault/secrets", headers=self._auth()
        )
        assert resp.status_code == 200
        assert "secrets" in resp.json()

    def test_revoke_secret_missing(self, vault_client):
        resp = vault_client.delete(
            "/api/organizations/org1/vault/secrets/missing", headers=self._auth()
        )
        assert resp.status_code == 404

    def test_rotate_secret(self, vault_client):
        resp = vault_client.post(
            "/api/organizations/org1/vault/secrets/stripe_key/rotate",
            headers=self._auth(),
        )
        assert resp.status_code == 200

    def test_test_secret(self, vault_client):
        resp = vault_client.post(
            "/api/organizations/org1/vault/secrets/stripe_key/test",
            headers=self._auth(),
        )
        assert resp.status_code == 200
        assert resp.json()["exists"] is True
