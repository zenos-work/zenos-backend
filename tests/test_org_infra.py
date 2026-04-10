"""Tests for Phase 3 Steps 17-19 — Org access, article security, org infra (audit, API keys, SSO)."""

import asyncio
import importlib
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
    import json as _json

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
            return _json.loads(self._body)

    class _Response:
        @staticmethod
        def new(body=None, status=200, headers=None):
            return _Resp(body=body, status=status, headers=headers)

    js_stub.Headers = _Headers
    js_stub.Response = _Response
    sys.modules["js"] = js_stub

# ── Imports ──────────────────────────────────────────────────────────────────
check_org_role_fn = importlib.import_module("middleware.org_access").check_org_role
article_security = importlib.import_module("middleware.article_security")
AuditLogEntry = importlib.import_module("models.org_infra.model").AuditLogEntry
ApiKey = importlib.import_module("models.org_infra.model").ApiKey
SsoConfig = importlib.import_module("models.org_infra.model").SsoConfig
infra_handler = importlib.import_module("api.org_infra.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ══════════════════════════════════════════════════════════════════════════════
# Step 17: Org access control middleware tests
# ══════════════════════════════════════════════════════════════════════════════
class TestCheckOrgRole:
    def test_owner_ge_admin(self):
        assert check_org_role_fn("owner", "admin") is True

    def test_admin_ge_admin(self):
        assert check_org_role_fn("admin", "admin") is True

    def test_editor_lt_admin(self):
        assert check_org_role_fn("editor", "admin") is False

    def test_member_ge_viewer(self):
        assert check_org_role_fn("member", "viewer") is True

    def test_viewer_ge_viewer(self):
        assert check_org_role_fn("viewer", "viewer") is True

    def test_none_role_fails(self):
        assert check_org_role_fn(None, "viewer") is False

    def test_owner_ge_owner(self):
        assert check_org_role_fn("owner", "owner") is True

    def test_admin_lt_owner(self):
        assert check_org_role_fn("admin", "owner") is False


# ══════════════════════════════════════════════════════════════════════════════
# Step 18: Article security model tests
# ══════════════════════════════════════════════════════════════════════════════
class TestArticleSecurityParams:
    def test_public_params_empty(self):
        assert article_security.security_params_public() == ()

    def test_org_member_params_length(self):
        params = article_security.security_params_org_member("org1", "u1")
        assert len(params) == 6
        assert params[0] == "org1"
        assert params[1] == "org1"
        assert params[2] == "u1"


# ══════════════════════════════════════════════════════════════════════════════
# Step 19: Org infra model tests
# ══════════════════════════════════════════════════════════════════════════════
class TestAuditLogModel:
    def test_from_row(self):
        row = {
            "id": "al1",
            "org_id": "org1",
            "actor_id": "u1",
            "actor_ip": "1.2.3.4",
            "action": "member.added",
            "resource": "org_members",
            "resource_id": "m1",
            "payload": '{"role":"editor"}',
            "created_at": "2026-01-01",
        }
        e = AuditLogEntry.from_row(row)
        assert e.action == "member.added"
        assert e.actor_ip == "1.2.3.4"

    def test_to_dict_public(self):
        e = AuditLogEntry(
            id="al1",
            action="member.added",
            created_at="2026-01-01",
            org_id="org1",
            actor_id="u1",
            actor_ip="1.2.3.4",
        )
        d = e.to_dict(scope="public")
        assert "actor_ip" not in d
        assert "org_id" not in d

    def test_to_dict_admin(self):
        e = AuditLogEntry(
            id="al1",
            action="member.added",
            created_at="2026-01-01",
            org_id="org1",
            actor_id="u1",
            actor_ip="1.2.3.4",
            payload='{"role":"editor"}',
        )
        d = e.to_dict(scope="admin")
        assert d["actor_ip"] == "1.2.3.4"
        assert d["org_id"] == "org1"
        assert d["payload"] == '{"role":"editor"}'


class TestApiKeyModel:
    def test_from_row(self):
        row = {
            "id": "k1",
            "org_id": "org1",
            "user_id": None,
            "name": "prod-key",
            "key_hash": "abc123",
            "key_prefix": "zk_abcd",
            "scopes": '["read","write"]',
            "last_used_at": None,
            "expires_at": None,
            "revoked_at": None,
            "created_by": "u1",
            "created_at": "2026-01-01",
        }
        k = ApiKey.from_row(row)
        assert k.name == "prod-key"
        assert k.key_prefix == "zk_abcd"

    def test_to_dict_public(self):
        k = ApiKey(
            id="k1",
            name="prod-key",
            key_prefix="zk_abcd",
            scopes='["read"]',
            created_by="u1",
            created_at="2026-01-01",
        )
        d = k.to_dict(scope="public")
        assert "key_hash" not in d
        assert "created_by" not in d

    def test_to_dict_admin(self):
        k = ApiKey(
            id="k1",
            name="prod-key",
            key_prefix="zk_abcd",
            scopes='["read"]',
            created_by="u1",
            created_at="2026-01-01",
            org_id="org1",
        )
        d = k.to_dict(scope="admin")
        assert d["created_by"] == "u1"
        assert d["org_id"] == "org1"


class TestSsoConfigModel:
    def test_from_row(self):
        row = {
            "id": "sso1",
            "org_id": "org1",
            "provider": "saml",
            "metadata": '{"entity_id":"..."}',
            "is_enabled": 1,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = SsoConfig.from_row(row)
        assert s.provider == "saml"
        assert s.is_enabled == 1

    def test_to_dict_public(self):
        s = SsoConfig(
            id="sso1",
            org_id="org1",
            provider="saml",
            metadata='{"entity_id":"..."}',
            is_enabled=1,
            created_by="u1",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = s.to_dict(scope="public")
        assert "metadata" not in d
        assert "created_by" not in d

    def test_to_dict_admin(self):
        s = SsoConfig(
            id="sso1",
            org_id="org1",
            provider="oidc",
            metadata='{"issuer":"..."}',
            is_enabled=0,
            created_by="u1",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = s.to_dict(scope="admin")
        assert d["metadata"] == '{"issuer":"..."}'
        assert d["created_by"] == "u1"


# ══════════════════════════════════════════════════════════════════════════════
# Org infra handler tests
# ══════════════════════════════════════════════════════════════════════════════
class FakeInfraService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_audit_log(self, org_id, page=1, limit=20):
        return {
            "audit_log": [{"id": "al1", "action": "member.added"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def create_api_key(self, org_id, name, scopes, created_by):
        return {
            "id": "k-new",
            "key": "raw-key-value",
            "key_prefix": "zk_abcd",
            "name": name,
        }

    async def list_api_keys(self, org_id, page=1, limit=20):
        return {
            "api_keys": [{"id": "k1", "name": "prod-key"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def revoke_api_key(self, key_id, org_id):
        pass

    async def create_sso(self, org_id, provider, metadata, is_enabled, created_by):
        if provider == "invalid":
            raise ValueError("Invalid provider: invalid")
        return {"id": "sso-new", "org_id": org_id, "provider": provider}

    async def update_sso(self, org_id, provider, metadata, is_enabled):
        if provider == "invalid":
            raise ValueError("Invalid provider: invalid")
        return {"id": "sso1", "org_id": org_id, "provider": provider}

    async def get_sso(self, org_id):
        if org_id == "no-sso":
            raise ValueError("No SSO config found")
        return {"id": "sso1", "org_id": org_id, "provider": "saml"}


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


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


# We need to mock require_org_role to avoid DB calls in tests
class InfraClient:
    def __init__(self, svc_instance, allowed_role="owner"):
        self.svc = svc_instance
        self.allowed_role = allowed_role

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _FakeDB:
            pass

        class _Env:
            JWT_SECRET = _JWT_SECRET
            DB = _FakeDB()

        allowed_role = self.allowed_role

        async def _mock_require_org_role(db, user_id, org_id, min_role):
            from middleware.org_access import ROLE_HIERARCHY

            if ROLE_HIERARCHY.get(allowed_role, -1) >= ROLE_HIERARCHY.get(min_role, 99):
                return allowed_role
            raise PermissionError(f"Requires org role '{min_role}' or higher")

        def _make_svc(_env, _ctx=None):
            return self.svc

        orig_svc = infra_handler.OrgInfraService
        orig_role = infra_handler.require_org_role
        infra_handler.OrgInfraService = _make_svc
        infra_handler.require_org_role = _mock_require_org_role
        try:
            return asyncio.run(
                infra_handler.handle_org_infra(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            infra_handler.OrgInfraService = orig_svc
            infra_handler.require_org_role = orig_role

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)


@pytest.fixture
def infra_svc():
    return FakeInfraService(None)


@pytest.fixture
def infra_client(infra_svc):
    return InfraClient(infra_svc, allowed_role="owner")


@pytest.fixture
def viewer_client(infra_svc):
    return InfraClient(infra_svc, allowed_role="viewer")


# ── Audit Log Tests ──────────────────────────────────────────────────────────
class TestAuditLogHandler:
    def test_list_audit_log(self, infra_client):
        resp = infra_client.get(
            "/api/organizations/org1/audit-log",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "audit_log" in resp.json()

    def test_list_audit_log_forbidden(self, viewer_client):
        resp = viewer_client.get(
            "/api/organizations/org1/audit-log",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 403


# ── API Key Tests ────────────────────────────────────────────────────────────
class TestApiKeyHandler:
    def test_create_api_key(self, infra_client):
        resp = infra_client.post(
            "/api/organizations/org1/api-keys",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "prod-key", "scopes": '["read","write"]'},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "prod-key"
        assert "key" in resp.json()

    def test_create_api_key_missing_name(self, infra_client):
        resp = infra_client.post(
            "/api/organizations/org1/api-keys",
            headers={"Authorization": f"Bearer {_token()}"},
            json={},
        )
        assert resp.status_code == 400

    def test_list_api_keys(self, infra_client):
        resp = infra_client.get(
            "/api/organizations/org1/api-keys",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "api_keys" in resp.json()

    def test_revoke_api_key(self, infra_client):
        resp = infra_client.delete(
            "/api/organizations/org1/api-keys/k1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_api_keys_forbidden(self, viewer_client):
        resp = viewer_client.get(
            "/api/organizations/org1/api-keys",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 403


# ── SSO Tests ────────────────────────────────────────────────────────────────
class TestSsoHandler:
    def test_create_sso(self, infra_client):
        resp = infra_client.post(
            "/api/organizations/org1/sso",
            headers={"Authorization": f"Bearer {_token()}"},
            json={
                "provider": "saml",
                "metadata": '{"entity_id":"..."}',
                "is_enabled": 1,
            },
        )
        assert resp.status_code == 201

    def test_create_sso_invalid_provider(self, infra_client):
        resp = infra_client.post(
            "/api/organizations/org1/sso",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"provider": "invalid"},
        )
        assert resp.status_code == 400

    def test_update_sso(self, infra_client):
        resp = infra_client.put(
            "/api/organizations/org1/sso",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"provider": "oidc", "metadata": '{"issuer":"..."}'},
        )
        assert resp.status_code == 200

    def test_get_sso(self, infra_client):
        resp = infra_client.get(
            "/api/organizations/org1/sso",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["provider"] == "saml"

    def test_get_sso_not_found(self, infra_client):
        resp = infra_client.get(
            "/api/organizations/no-sso/sso",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_sso_forbidden_non_owner(self, viewer_client):
        resp = viewer_client.post(
            "/api/organizations/org1/sso",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"provider": "saml"},
        )
        assert resp.status_code == 403

    def test_unauth(self, infra_client):
        resp = infra_client.get("/api/organizations/org1/sso")
        assert resp.status_code == 401
