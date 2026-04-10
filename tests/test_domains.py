"""Tests for Phase 2 Step 13 — Custom Domains (model + service + handler)."""

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

CustomDomain = importlib.import_module("models.domain.model").CustomDomain
domain_handler = importlib.import_module("api.domains.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestCustomDomainModel:
    def test_from_row(self):
        row = {
            "id": "d1",
            "domain": "blog.example.com",
            "resource_type": "blog",
            "verification_status": "pending",
            "verification_method": "cname",
            "verification_token": "abc123",
            "ssl_status": "pending",
            "is_active": 0,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "org_id": None,
            "user_id": "u1",
            "resource_id": None,
            "verified_at": None,
            "ssl_issued_at": None,
            "ssl_expires_at": None,
            "redirect_to": None,
        }
        d = CustomDomain.from_row(row)
        assert d.domain == "blog.example.com"
        assert d.verification_status == "pending"

    def test_to_dict(self):
        d = CustomDomain(
            id="d1",
            domain="blog.example.com",
            resource_type="blog",
            verification_status="verified",
            verification_method="cname",
            verification_token="abc123",
            ssl_status="active",
            is_active=1,
            created_at="2026-01-01",
            updated_at="2026-01-02",
            user_id="u1",
        )
        data = d.to_dict()
        assert data["domain"] == "blog.example.com"
        assert data["is_active"] is True
        assert data["user_id"] == "u1"


# ── Fake Service ──
class FakeDomainService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def register_domain(
        self,
        user_id,
        domain,
        resource_type,
        verification_method="cname",
        org_id=None,
        resource_id=None,
    ):
        self.calls.append(("register_domain", user_id, domain))
        if domain == "taken.com":
            raise ValueError("Domain already registered")
        if resource_type not in {"blog", "publication"}:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        return {"id": "new-domain-id", "verification_token": "tok123"}

    async def list_domains(self, user_id, page=1, limit=20):
        self.calls.append(("list_domains", user_id))
        return {
            "domains": [{"id": "d1", "domain": "blog.example.com"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def verify_domain(self, domain_id, user_id):
        self.calls.append(("verify_domain", domain_id, user_id))
        if domain_id == "missing":
            raise ValueError("Domain not found")
        return {"id": domain_id, "verification_status": "verified"}

    async def delete_domain(self, domain_id, user_id):
        self.calls.append(("delete_domain", domain_id, user_id))
        if domain_id == "missing":
            raise ValueError("Domain not found")


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


class DomainClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )
        svc = self.svc

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return svc

        orig = domain_handler.DomainService
        domain_handler.DomainService = _make_svc
        try:
            return asyncio.run(
                domain_handler.handle_domains(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            domain_handler.DomainService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeDomainService(_Env())


@pytest.fixture
def client(svc):
    return DomainClient(svc)


# ── Handler Tests ──
class TestDomainHandler:
    def test_register_domain(self, client, svc):
        resp = client.post(
            "/api/domains",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"domain": "blog.example.com", "resource_type": "blog"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["verification_token"] == "tok123"

    def test_register_taken_domain(self, client, svc):
        resp = client.post(
            "/api/domains",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"domain": "taken.com", "resource_type": "blog"},
        )
        assert resp.status_code == 400

    def test_list_domains(self, client, svc):
        resp = client.get(
            "/api/domains",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "domains" in resp.json()

    def test_verify_domain(self, client, svc):
        resp = client.post(
            "/api/domains/d1/verify",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["verification_status"] == "verified"

    def test_verify_missing_domain(self, client, svc):
        resp = client.post(
            "/api/domains/missing/verify",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 400

    def test_delete_domain(self, client, svc):
        resp = client.delete(
            "/api/domains/d1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

    def test_delete_missing_domain(self, client, svc):
        resp = client.delete(
            "/api/domains/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_unauth(self, client):
        resp = client.get("/api/domains")
        assert resp.status_code == 401
