"""Tests for Phase 3 Steps 15-16 — Organizations + Add-ons (model + service + handler)."""

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

Organization = importlib.import_module("models.organization.model").Organization
OrgMember = importlib.import_module("models.organization.model").OrgMember
Team = importlib.import_module("models.organization.model").Team
OrgInvitation = importlib.import_module("models.organization.model").OrgInvitation
OrgAddOn = importlib.import_module("models.add_on.model").OrgAddOn
require_add_on = importlib.import_module("models.add_on.model").require_add_on
org_handler = importlib.import_module("api.organizations.handler")
addon_handler = importlib.import_module("api.add_ons.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──────────────────────────────────────────────────────────────
class TestOrganizationModel:
    def test_from_row(self):
        row = {
            "id": "org1",
            "name": "Acme",
            "slug": "acme",
            "plan_tier": "free",
            "plan_status": "active",
            "max_members": 5,
            "max_workflows": 3,
            "max_leads": 1000,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "subdomain": None,
            "logo_url": None,
            "website": None,
            "description": "A corp",
            "trial_ends_at": None,
            "plan_started_at": None,
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "settings": "{}",
        }
        o = Organization.from_row(row)
        assert o.id == "org1"
        assert o.name == "Acme"
        assert o.plan_tier == "free"

    def test_to_dict_public(self):
        o = Organization(
            id="org1",
            name="Acme",
            slug="acme",
            plan_tier="free",
            plan_status="active",
            max_members=5,
            max_workflows=3,
            max_leads=1000,
            created_by="u1",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = o.to_dict(scope="public")
        assert "created_by" not in d
        assert "max_workflows" not in d

    def test_to_dict_admin(self):
        o = Organization(
            id="org1",
            name="Acme",
            slug="acme",
            plan_tier="business",
            plan_status="active",
            max_members=50,
            max_workflows=25,
            max_leads=10000,
            created_by="u1",
            created_at="2026-01-01",
            updated_at="2026-01-01",
            settings='{"custom": true}',
        )
        d = o.to_dict(scope="admin")
        assert d["max_workflows"] == 25
        assert d["created_by"] == "u1"
        assert d["settings"] == '{"custom": true}'


class TestOrgMemberModel:
    def test_from_row(self):
        row = {
            "id": "m1",
            "org_id": "org1",
            "user_id": "u1",
            "org_role": "admin",
            "joined_at": "2026-01-01",
            "invited_by": "u0",
        }
        m = OrgMember.from_row(row)
        assert m.org_role == "admin"
        assert m.invited_by == "u0"


class TestOrgInvitationModel:
    def test_from_row(self):
        row = {
            "id": "inv1",
            "org_id": "org1",
            "email": "new@example.com",
            "org_role": "member",
            "token": "tok123",
            "status": "pending",
            "invited_by": "u1",
            "expires_at": "2099-12-31",
            "created_at": "2026-01-01",
            "team_id": None,
            "accepted_at": None,
        }
        inv = OrgInvitation.from_row(row)
        assert inv.token == "tok123"
        assert inv.status == "pending"

    def test_to_dict_public_hides_token(self):
        inv = OrgInvitation(
            id="inv1",
            org_id="org1",
            email="new@example.com",
            org_role="member",
            token="tok123",
            status="pending",
            invited_by="u1",
            expires_at="2099-12-31",
            created_at="2026-01-01",
        )
        d = inv.to_dict(scope="public")
        assert "token" not in d
        assert "invited_by" not in d

    def test_to_dict_admin_shows_token(self):
        inv = OrgInvitation(
            id="inv1",
            org_id="org1",
            email="new@example.com",
            org_role="member",
            token="tok123",
            status="pending",
            invited_by="u1",
            expires_at="2099-12-31",
            created_at="2026-01-01",
        )
        d = inv.to_dict(scope="admin")
        assert d["token"] == "tok123"
        assert d["invited_by"] == "u1"


class TestOrgAddOnModel:
    def test_from_row(self):
        row = {
            "id": "ao1",
            "org_id": "org1",
            "add_on_type": "workflow_builder",
            "tier": "pro",
            "is_active": 1,
            "enabled_by": "u1",
            "limits": '{"max_workflows": 25}',
            "started_at": "2026-01-01",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "stripe_subscription_id": None,
            "trial_ends_at": None,
            "expires_at": None,
        }
        a = OrgAddOn.from_row(row)
        assert a.add_on_type == "workflow_builder"
        assert a.tier == "pro"

    def test_require_add_on_active(self):
        a = OrgAddOn(
            id="ao1",
            org_id="org1",
            add_on_type="workflow_builder",
            tier="pro",
            is_active=1,
            enabled_by="u1",
            limits="{}",
            started_at="",
            created_at="",
            updated_at="",
        )
        assert require_add_on(a) == a

    def test_require_add_on_inactive(self):
        a = OrgAddOn(
            id="ao1",
            org_id="org1",
            add_on_type="workflow_builder",
            tier="pro",
            is_active=0,
            enabled_by="u1",
            limits="{}",
            started_at="",
            created_at="",
            updated_at="",
        )
        with pytest.raises(PermissionError):
            require_add_on(a)

    def test_require_add_on_tier_insufficient(self):
        a = OrgAddOn(
            id="ao1",
            org_id="org1",
            add_on_type="workflow_builder",
            tier="basic",
            is_active=1,
            enabled_by="u1",
            limits="{}",
            started_at="",
            created_at="",
            updated_at="",
        )
        with pytest.raises(PermissionError, match="Tier"):
            require_add_on(a, min_tier="pro")


# ── Fake Services ────────────────────────────────────────────────────────────
class FakeOrgService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def create_org(self, user_id, name, description=None):
        self.calls.append(("create_org", user_id, name))
        return {"id": "org-new", "name": name, "slug": "acme-abc"}

    async def list_user_orgs(self, user_id, page=1, limit=20):
        return {
            "organizations": [{"id": "org1"}],
            "pagination": {"page": 1, "limit": 20, "total": 1, "pages": 1},
        }

    async def get_org(self, org_id, user_id):
        if org_id == "missing":
            raise ValueError("Organization not found")
        return {"id": org_id, "name": "Acme"}

    async def update_org(
        self, org_id, user_id, name, description=None, logo_url=None, website=None
    ):
        return {"id": org_id, "name": name}

    async def list_members(self, org_id, user_id, page=1, limit=20):
        return {
            "members": [{"user_id": "u1"}],
            "pagination": {"page": 1, "limit": 20, "total": 1, "pages": 1},
        }

    async def add_member(self, org_id, actor_id, target_user_id, role="member"):
        if target_user_id == "dup":
            raise ValueError("User is already a member")
        return {
            "id": "m-new",
            "org_id": org_id,
            "user_id": target_user_id,
            "org_role": role,
        }

    async def update_member_role(self, org_id, actor_id, target_user_id, role):
        return {"org_id": org_id, "user_id": target_user_id, "org_role": role}

    async def remove_member(self, org_id, actor_id, target_user_id):
        if target_user_id == "owner-user":
            raise ValueError("Cannot remove the owner")

    async def create_team(self, org_id, actor_id, name, description=None):
        return {"id": "t-new", "org_id": org_id, "name": name}

    async def list_teams(self, org_id, user_id, page=1, limit=20):
        return {
            "teams": [{"id": "t1"}],
            "pagination": {"page": 1, "limit": 20, "total": 1, "pages": 1},
        }

    async def add_team_member(self, org_id, actor_id, team_id, user_id):
        return {"team_id": team_id, "user_id": user_id}

    async def remove_team_member(self, org_id, actor_id, team_id, user_id):
        pass

    async def create_invitation(self, org_id, actor_id, email, role="member"):
        return {"id": "inv-new", "token": "tok-abc", "email": email, "org_role": role}

    async def accept_invitation(self, token, user_id):
        if token == "bad-token":
            raise ValueError("Invitation not found or expired")
        return {"org_id": "org1", "org_role": "member"}

    async def delete_invitation(self, org_id, actor_id, inv_id):
        pass

    async def list_invitations(self, org_id, actor_id, page=1, limit=20):
        return {
            "invitations": [],
            "pagination": {"page": 1, "limit": 20, "total": 0, "pages": 0},
        }


class FakeAddOnService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def enable_add_on(self, org_id, add_on_type, tier, enabled_by, limits="{}"):
        if add_on_type == "invalid":
            raise ValueError("Invalid add-on type: invalid")
        self.calls.append(("enable", org_id, add_on_type))
        return {"id": "ao-new", "add_on_type": add_on_type, "tier": tier}

    async def update_add_on(self, org_id, add_on_type, tier, limits="{}"):
        if add_on_type == "missing":
            raise ValueError("Add-on not found")
        return {"add_on_type": add_on_type, "tier": tier}

    async def disable_add_on(self, org_id, add_on_type):
        if add_on_type == "missing":
            raise ValueError("Add-on not found")

    async def list_add_ons(self, org_id):
        return {"add_ons": [{"add_on_type": "workflow_builder"}]}

    async def get_usage(self, org_id, add_on_type):
        if add_on_type == "missing":
            raise ValueError("Add-on not found")
        return {
            "add_on_type": add_on_type,
            "tier": "pro",
            "limits": "{}",
            "is_active": 1,
        }

    async def summary(self):
        return {"summary": [{"add_on_type": "workflow_builder", "count": 5}]}


# ── Test Helpers ─────────────────────────────────────────────────────────────
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


def _admin_token():
    return create_token({"sub": "admin-user", "role": "SUPERADMIN"}, _JWT_SECRET)


class OrgClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return self.svc

        orig = org_handler.OrganizationService
        org_handler.OrganizationService = _make_svc
        try:
            return asyncio.run(
                org_handler.handle_organizations(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            org_handler.OrganizationService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)


class InviteClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def post(self, path, headers=None, json=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method="POST", url=path, headers=headers or {}, json_body=json
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return self.svc

        orig = org_handler.OrganizationService
        org_handler.OrganizationService = _make_svc
        try:
            return asyncio.run(
                org_handler.handle_invitation_accept(
                    req, _Env(), parsed.path, "POST", parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            org_handler.OrganizationService = orig


class AddOnClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        def _make_svc(_env, _ctx=None):
            return self.svc

        orig = addon_handler.AddOnService
        addon_handler.AddOnService = _make_svc
        try:
            return asyncio.run(
                addon_handler.handle_add_ons(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            addon_handler.AddOnService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def org_svc():
    class _Env:
        pass

    return FakeOrgService(_Env())


@pytest.fixture
def org_client(org_svc):
    return OrgClient(org_svc)


@pytest.fixture
def invite_client(org_svc):
    return InviteClient(org_svc)


@pytest.fixture
def addon_svc():
    class _Env:
        pass

    return FakeAddOnService(_Env())


@pytest.fixture
def addon_client(addon_svc):
    return AddOnClient(addon_svc)


# ── Organization Handler Tests ───────────────────────────────────────────────
class TestOrgHandler:
    def test_create_org(self, org_client):
        resp = org_client.post(
            "/api/organizations",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "Acme Corp"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Acme Corp"

    def test_create_org_missing_name(self, org_client):
        resp = org_client.post(
            "/api/organizations",
            headers={"Authorization": f"Bearer {_token()}"},
            json={},
        )
        assert resp.status_code == 400

    def test_list_orgs(self, org_client):
        resp = org_client.get(
            "/api/organizations",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "organizations" in resp.json()

    def test_get_org(self, org_client):
        resp = org_client.get(
            "/api/organizations/org1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == "org1"

    def test_get_org_not_found(self, org_client):
        resp = org_client.get(
            "/api/organizations/missing",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404

    def test_update_org(self, org_client):
        resp = org_client.put(
            "/api/organizations/org1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "New Name"},
        )
        assert resp.status_code == 200

    def test_list_members(self, org_client):
        resp = org_client.get(
            "/api/organizations/org1/members",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "members" in resp.json()

    def test_add_member(self, org_client):
        resp = org_client.post(
            "/api/organizations/org1/members",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"user_id": "u2", "role": "editor"},
        )
        assert resp.status_code == 201

    def test_add_duplicate_member(self, org_client):
        resp = org_client.post(
            "/api/organizations/org1/members",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"user_id": "dup"},
        )
        assert resp.status_code == 400

    def test_update_member_role(self, org_client):
        resp = org_client.put(
            "/api/organizations/org1/members/u2",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"role": "admin"},
        )
        assert resp.status_code == 200

    def test_remove_member(self, org_client):
        resp = org_client.delete(
            "/api/organizations/org1/members/u2",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_remove_owner_fails(self, org_client):
        resp = org_client.delete(
            "/api/organizations/org1/members/owner-user",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 400

    def test_create_team(self, org_client):
        resp = org_client.post(
            "/api/organizations/org1/teams",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"name": "Engineering"},
        )
        assert resp.status_code == 201

    def test_list_teams(self, org_client):
        resp = org_client.get(
            "/api/organizations/org1/teams",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "teams" in resp.json()

    def test_add_team_member(self, org_client):
        resp = org_client.post(
            "/api/organizations/org1/teams/t1/members",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"user_id": "u2"},
        )
        assert resp.status_code == 201

    def test_remove_team_member(self, org_client):
        resp = org_client.delete(
            "/api/organizations/org1/teams/t1/members/u2",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_create_invitation(self, org_client):
        resp = org_client.post(
            "/api/organizations/org1/invitations",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"email": "new@example.com", "role": "member"},
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "new@example.com"

    def test_list_invitations(self, org_client):
        resp = org_client.get(
            "/api/organizations/org1/invitations",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "invitations" in resp.json()

    def test_delete_invitation(self, org_client):
        resp = org_client.delete(
            "/api/organizations/org1/invitations/inv1",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_unauth(self, org_client):
        resp = org_client.get("/api/organizations")
        assert resp.status_code == 401


# ── Invitation Accept Handler Tests ──────────────────────────────────────────
class TestInvitationAcceptHandler:
    def test_accept_invitation(self, invite_client):
        resp = invite_client.post(
            "/api/invitations/tok-abc/accept",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["org_id"] == "org1"

    def test_accept_bad_token(self, invite_client):
        resp = invite_client.post(
            "/api/invitations/bad-token/accept",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 400


# ── Add-On Handler Tests ────────────────────────────────────────────────────
class TestAddOnHandler:
    def test_admin_enable_add_on(self, addon_client):
        resp = addon_client.post(
            "/api/admin/organizations/org1/add-ons",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json={"add_on_type": "workflow_builder", "tier": "pro"},
        )
        assert resp.status_code == 201

    def test_admin_enable_invalid_type(self, addon_client):
        resp = addon_client.post(
            "/api/admin/organizations/org1/add-ons",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json={"add_on_type": "invalid"},
        )
        assert resp.status_code == 400

    def test_admin_list_add_ons(self, addon_client):
        resp = addon_client.get(
            "/api/admin/organizations/org1/add-ons",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert "add_ons" in resp.json()

    def test_admin_update_add_on(self, addon_client):
        resp = addon_client.put(
            "/api/admin/organizations/org1/add-ons/workflow_builder",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json={"tier": "unlimited"},
        )
        assert resp.status_code == 200

    def test_admin_disable_add_on(self, addon_client):
        resp = addon_client.delete(
            "/api/admin/organizations/org1/add-ons/workflow_builder",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200

    def test_admin_summary(self, addon_client):
        resp = addon_client.get(
            "/api/admin/add-ons/summary",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert "summary" in resp.json()

    def test_non_admin_forbidden(self, addon_client):
        resp = addon_client.post(
            "/api/admin/organizations/org1/add-ons",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"add_on_type": "workflow_builder"},
        )
        assert resp.status_code == 403

    def test_org_list_add_ons(self, addon_client):
        resp = addon_client.get(
            "/api/organizations/org1/add-ons",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_org_get_usage(self, addon_client):
        resp = addon_client.get(
            "/api/organizations/org1/add-ons/workflow_builder/usage",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200

    def test_org_get_usage_missing(self, addon_client):
        resp = addon_client.get(
            "/api/organizations/org1/add-ons/missing/usage",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 404
