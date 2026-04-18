"""Tests for Phase 3.5 — Feature Flags (model + service + handler)."""

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

FeatureFlag = importlib.import_module("models.feature_flag.model").FeatureFlag
VALID_CATEGORIES = importlib.import_module("models.feature_flag.model").VALID_CATEGORIES
VALID_TARGET_TYPES = importlib.import_module(
    "models.feature_flag.model"
).VALID_TARGET_TYPES
ff_handler = importlib.import_module("api.feature_flags.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════
class TestFeatureFlagModel:
    def test_from_row_basic(self):
        row = {
            "id": "ff1",
            "flag_key": "pdf_export",
            "name": "PDF Export",
            "description": "Allow PDF export",
            "category": "content",
            "is_active": 1,
            "target_type": "global",
            "targets": "[]",
            "rollout_pct": 0,
            "metadata": "{}",
            "created_by": "admin",
            "updated_by": None,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        f = FeatureFlag.from_row(row)
        assert f.id == "ff1"
        assert f.flag_key == "pdf_export"
        assert f.is_active is True
        assert f.targets == []
        assert f.metadata == {}

    def test_from_row_none(self):
        assert FeatureFlag.from_row(None) is None

    def test_to_dict_public(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="test",
            name="Test",
            category="general",
            is_active=True,
            target_type="global",
            targets=[],
            rollout_pct=0,
            created_by="admin",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = f.to_dict(scope="public")
        assert "flag_key" in d
        assert "created_by" not in d

    def test_to_dict_admin(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="test",
            name="Test",
            category="general",
            is_active=True,
            target_type="global",
            targets=[],
            rollout_pct=0,
            created_by="admin1",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = f.to_dict(scope="admin")
        assert d["created_by"] == "admin1"

    def test_evaluate_global_active(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="global",
            targets=[],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate() is True

    def test_evaluate_inactive(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=False,
            target_type="global",
            targets=[],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate() is False

    def test_evaluate_user_list_match(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="user_ids",
            targets=["u1", "u2"],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(user_id="u1") is True
        assert f.evaluate(user_id="u99") is False

    def test_evaluate_role_list(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="user_roles",
            targets=["SUPERADMIN"],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(user_role="SUPERADMIN") is True
        assert f.evaluate(user_role="AUTHOR") is False

    def test_evaluate_org_list(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="org_ids",
            targets=["org1"],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(org_id="org1") is True
        assert f.evaluate(org_id="org99") is False

    def test_evaluate_org_tiers(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="org_tiers",
            targets=["business", "enterprise"],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(org_tier="business") is True
        assert f.evaluate(org_tier="free") is False

    def test_evaluate_membership_tiers(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="membership_tiers",
            targets=["premium"],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(membership_tier="premium") is True
        assert f.evaluate(membership_tier="free") is False

    def test_evaluate_percentage(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="percentage",
            targets=[],
            rollout_pct=100,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(user_id="any-user") is True

    def test_evaluate_percentage_zero(self):
        f = FeatureFlag(
            id="ff1",
            flag_key="t",
            name="T",
            category="general",
            is_active=True,
            target_type="percentage",
            targets=[],
            rollout_pct=0,
            created_by="",
            created_at="",
            updated_at="",
        )
        assert f.evaluate(user_id="any-user") is False


# ═══════════════════════════════════════════════════════════════
# Fake Service
# ═══════════════════════════════════════════════════════════════
class FakeFeatureFlagService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def evaluate_all(
        self,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ):
        self.calls.append(("evaluate_all", user_id))
        return {"pdf_export": True, "workflow_builder": False}

    async def evaluate_one(
        self,
        flag_key,
        user_id=None,
        user_role=None,
        org_id=None,
        org_tier=None,
        membership_tier=None,
    ):
        self.calls.append(("evaluate_one", flag_key))
        return flag_key == "pdf_export"

    async def list_flags(self, category=None):
        self.calls.append(("list_flags", category))
        return {
            "flags": [{"id": "ff1", "flag_key": "pdf_export", "is_active": True}],
            "total": 1,
        }

    async def get_flag(self, flag_id):
        self.calls.append(("get_flag", flag_id))
        if flag_id == "missing":
            raise ValueError("Flag not found")
        return {"id": flag_id, "flag_key": "pdf_export", "is_active": True}

    async def create_flag(
        self,
        flag_key,
        name,
        created_by,
        description="",
        category="general",
        is_active=False,
        target_type="global",
        targets=None,
        rollout_pct=0,
        metadata=None,
    ):
        self.calls.append(("create_flag", flag_key))
        if category == "bad":
            raise ValueError(f"Invalid category: {category}")
        if flag_key == "duplicate":
            raise ValueError("Flag key 'duplicate' already exists")
        return {"id": "new-ff-id", "flag_key": flag_key}

    async def update_flag(self, flag_id, updated_by, **kwargs):
        self.calls.append(("update_flag", flag_id))
        if flag_id == "missing":
            raise ValueError("Flag not found")
        return {"id": flag_id, "flag_key": "pdf_export", "is_active": True}

    async def delete_flag(self, flag_id):
        self.calls.append(("delete_flag", flag_id))
        if flag_id == "missing":
            raise ValueError("Flag not found")

    async def toggle_flag(self, flag_id, updated_by):
        self.calls.append(("toggle_flag", flag_id))
        if flag_id == "missing":
            raise ValueError("Flag not found")
        return {"id": flag_id, "is_active": False}

    async def preview_announcement(self, payload):
        self.calls.append(("preview_announcement", payload.get("flag_key")))
        return {
            "action": payload.get("action", "enabled"),
            "message": "Preview message",
            "scope": "global",
            "channels": ["in_app", "email"],
            "recipient_count": 12,
            "channel_recipient_counts": {"in_app": 12, "email": 4},
        }


# ═══════════════════════════════════════════════════════════════
# Test helpers
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


class FFClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None):
        return self._dispatch("DELETE", path, headers=headers)

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig = ff_handler.FeatureFlagService
        ff_handler.FeatureFlagService = lambda env, ctx=None: self.svc
        try:
            return asyncio.run(
                ff_handler.handle_feature_flags(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            ff_handler.FeatureFlagService = orig


def _token(sub="u1", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


def _admin_token():
    return create_token({"sub": "sa1", "role": "SUPERADMIN"}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeFeatureFlagService(_Env())


@pytest.fixture
def client(svc):
    return FFClient(svc)


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Public
# ═══════════════════════════════════════════════════════════════
class TestFeatureFlagsPublic:
    def test_evaluate_all_flags(self, client, svc):
        resp = client.get(
            "/api/features",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "flags" in data
        assert data["flags"]["pdf_export"] is True
        assert svc.calls[-1][0] == "evaluate_all"

    def test_evaluate_single_flag(self, client, svc):
        resp = client.get(
            "/api/features/pdf_export",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["flag_key"] == "pdf_export"
        assert data["enabled"] is True

    def test_evaluate_disabled_flag(self, client, svc):
        resp = client.get(
            "/api/features/workflow_builder",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_unauthenticated(self, client):
        resp = client.get("/api/features")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Admin CRUD
# ═══════════════════════════════════════════════════════════════
class TestFeatureFlagsAdmin:
    def test_list_flags(self, client, svc):
        resp = client.get(
            "/api/admin/feature-flags",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_flags_forbidden_for_author(self, client):
        resp = client.get(
            "/api/admin/feature-flags",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 403

    def test_get_flag(self, client, svc):
        resp = client.get(
            "/api/admin/feature-flags/ff1",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == "ff1"

    def test_get_flag_missing(self, client, svc):
        resp = client.get(
            "/api/admin/feature-flags/missing",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 404

    def test_create_flag(self, client, svc):
        resp = client.post(
            "/api/admin/feature-flags",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={
                "flag_key": "new_feature",
                "name": "New Feature",
                "category": "general",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["flag_key"] == "new_feature"

    def test_preview_announcement(self, client, svc):
        resp = client.post(
            "/api/admin/feature-flags/preview-announcement",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={
                "flag_key": "preview_feature",
                "name": "Preview Feature",
                "action": "enabled",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Preview message"
        assert resp.json()["channels"] == ["in_app", "email"]

    def test_create_flag_invalid_category(self, client, svc):
        resp = client.post(
            "/api/admin/feature-flags",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={"flag_key": "test", "name": "Test", "category": "bad"},
        )
        assert resp.status_code == 400

    def test_create_duplicate_flag(self, client, svc):
        resp = client.post(
            "/api/admin/feature-flags",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={"flag_key": "duplicate", "name": "Dup"},
        )
        assert resp.status_code == 400

    def test_update_flag(self, client, svc):
        resp = client.put(
            "/api/admin/feature-flags/ff1",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={"name": "Updated Name"},
        )
        assert resp.status_code == 200

    def test_update_missing_flag(self, client, svc):
        resp = client.put(
            "/api/admin/feature-flags/missing",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 400

    def test_toggle_flag(self, client, svc):
        resp = client.put(
            "/api/admin/feature-flags/ff1/toggle",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_toggle_missing_flag(self, client, svc):
        resp = client.put(
            "/api/admin/feature-flags/missing/toggle",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 404

    def test_delete_flag(self, client, svc):
        resp = client.delete(
            "/api/admin/feature-flags/ff1",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_missing_flag(self, client, svc):
        resp = client.delete(
            "/api/admin/feature-flags/missing",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 404
