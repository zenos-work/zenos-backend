"""Tests for Phase 6 — Analytics, Metering & Dashboards (model + handler)."""

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

# ── Model imports ───────────────────────────────────────────
ana_models = importlib.import_module("models.analytics.model")
AnalyticsEvent = ana_models.AnalyticsEvent
ConversionGoal = ana_models.ConversionGoal
ConversionEvent = ana_models.ConversionEvent
FunnelDefinition = ana_models.FunnelDefinition
FunnelStep = ana_models.FunnelStep
AbExperiment = ana_models.AbExperiment
AbExperimentVariant = ana_models.AbExperimentVariant

ana_handler = importlib.import_module("api.analytics.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsModels:
    def test_analytics_event_from_row(self):
        row = {
            "id": "ev1",
            "org_id": "org1",
            "event_category": "pageview",
            "event_action": "view",
            "event_label": "",
            "event_value": 0,
            "resource_type": "article",
            "resource_id": "a1",
            "user_id": "u1",
            "anonymous_id": "",
            "session_id": "s1",
            "page_url": "",
            "referrer_url": "",
            "utm_source": "google",
            "utm_medium": "",
            "utm_campaign": "",
            "country_code": "US",
            "device_type": "",
            "properties": '{"key":"val"}',
            "created_at": "2026-01-01",
        }
        e = AnalyticsEvent.from_row(row)
        assert e.event_category == "pageview"
        assert e.properties == {"key": "val"}
        assert e.country_code == "US"

    def test_analytics_event_from_row_none(self):
        assert AnalyticsEvent.from_row(None) is None

    def test_conversion_goal_from_row(self):
        row = {
            "id": "g1",
            "org_id": "org1",
            "name": "Sign Up",
            "goal_type": "event",
            "target_event_category": "auth",
            "target_event_action": "signup",
            "target_resource_id": "",
            "value_cents": 500,
            "is_active": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        g = ConversionGoal.from_row(row)
        assert g.name == "Sign Up"
        assert g.value_cents == 500
        assert g.is_active is True

    def test_conversion_event_from_row(self):
        row = {
            "id": "ce1",
            "goal_id": "g1",
            "org_id": "org1",
            "user_id": "u1",
            "anonymous_id": "",
            "session_id": "s1",
            "event_id": "ev1",
            "value_cents": 500,
            "created_at": "2026-01-01",
        }
        c = ConversionEvent.from_row(row)
        assert c.goal_id == "g1"
        assert c.value_cents == 500

    def test_funnel_definition_from_row(self):
        row = {
            "id": "f1",
            "org_id": "org1",
            "name": "Onboarding",
            "description": "User onboarding funnel",
            "is_active": 1,
            "created_by": "u1",
            "created_at": "2026-01-01",
        }
        f = FunnelDefinition.from_row(row)
        assert f.name == "Onboarding"
        assert f.is_active is True

    def test_funnel_step_from_row(self):
        row = {
            "id": "fs1",
            "funnel_id": "f1",
            "step_number": 1,
            "name": "Sign Up",
            "event_category": "auth",
            "event_action": "signup",
            "resource_type": "",
            "resource_id": "",
            "created_at": "2026-01-01",
        }
        s = FunnelStep.from_row(row)
        assert s.step_number == 1
        assert s.name == "Sign Up"

    def test_ab_experiment_from_row(self):
        row = {
            "id": "exp1",
            "org_id": "org1",
            "name": "CTA Color",
            "hypothesis": "Red works better",
            "status": "running",
            "traffic_split": '{"control":50,"variant":50}',
            "success_goal_id": "g1",
            "winner_variant_id": None,
            "started_at": "2026-01-01",
            "ended_at": None,
            "created_by": "u1",
            "created_at": "2026-01-01",
        }
        e = AbExperiment.from_row(row)
        assert e.name == "CTA Color"
        assert e.traffic_split == {"control": 50, "variant": 50}
        assert e.status == "running"

    def test_ab_experiment_variant_from_row(self):
        row = {
            "id": "v1",
            "experiment_id": "exp1",
            "name": "Red",
            "description": "Red CTA button",
            "changes": '{"color":"red"}',
            "impressions": 100,
            "conversions": 10,
            "created_at": "2026-01-01",
        }
        v = AbExperimentVariant.from_row(row)
        assert v.name == "Red"
        assert v.changes == {"color": "red"}
        assert v.impressions == 100


# ═══════════════════════════════════════════════════════════════
# Fake Analytics Service
# ═══════════════════════════════════════════════════════════════
class FakeAnalyticsService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Events
    async def list_analytics_events(self, org_id, page=1, limit=50):
        self.calls.append(("list_analytics_events", org_id))
        return {"events": [{"id": "ev1"}], "total": 1, "page": page, "limit": limit}

    async def track_event(self, org_id, event_category, event_action, **kw):
        self.calls.append(("track_event", org_id, event_category))
        if not org_id:
            raise ValueError("org_id required")
        return {"id": "new-evt"}

    # Goals
    async def list_goals(self, org_id):
        self.calls.append(("list_goals", org_id))
        return [{"id": "g1", "name": "Sign Up"}]

    async def get_goal(self, gid):
        self.calls.append(("get_goal", gid))
        if gid == "missing":
            raise ValueError("Goal not found")
        return {"id": gid}

    async def create_goal(self, org_id, name, goal_type, **kw):
        self.calls.append(("create_goal", org_id))
        return {"id": "new-goal"}

    async def update_goal(self, gid, **kw):
        self.calls.append(("update_goal", gid))
        if gid == "missing":
            raise ValueError("Goal not found")
        return {"id": gid}

    async def delete_goal(self, gid):
        self.calls.append(("delete_goal", gid))
        if gid == "missing":
            raise ValueError("Goal not found")

    # Conversions
    async def list_conversions(self, goal_id, page=1, limit=50):
        self.calls.append(("list_conversions", goal_id))
        return {
            "conversions": [{"id": "ce1"}],
            "total": 1,
            "page": page,
            "limit": limit,
        }

    async def record_conversion(
        self,
        goal_id,
        org_id,
        user_id="",
        anonymous_id="",
        session_id="",
        event_id="",
        value_cents=0,
    ):
        self.calls.append(("record_conversion", goal_id))
        return {"id": "new-conv"}

    # Funnels
    async def list_funnels(self, org_id):
        self.calls.append(("list_funnels", org_id))
        return [{"id": "f1"}]

    async def get_funnel(self, fid):
        self.calls.append(("get_funnel", fid))
        if fid == "missing":
            raise ValueError("Funnel not found")
        return {"id": fid}

    async def create_funnel(
        self, org_id, name, description="", is_active=True, created_by=""
    ):
        self.calls.append(("create_funnel", org_id))
        return {"id": "new-funnel"}

    async def update_funnel(self, fid, **kw):
        self.calls.append(("update_funnel", fid))
        if fid == "missing":
            raise ValueError("Funnel not found")
        return {"id": fid}

    async def delete_funnel(self, fid):
        self.calls.append(("delete_funnel", fid))
        if fid == "missing":
            raise ValueError("Funnel not found")

    # Funnel Steps
    async def list_funnel_steps(self, funnel_id):
        self.calls.append(("list_funnel_steps", funnel_id))
        return [{"id": "fs1", "step_number": 1}]

    async def create_funnel_step(
        self,
        funnel_id,
        step_number=0,
        name="",
        event_category="",
        event_action="",
        resource_type="",
        resource_id="",
    ):
        self.calls.append(("create_funnel_step", funnel_id))
        return {"id": "new-step"}

    async def delete_funnel_step(self, step_id):
        self.calls.append(("delete_funnel_step", step_id))

    # Experiments
    async def list_experiments(self, org_id):
        self.calls.append(("list_experiments", org_id))
        return [{"id": "exp1"}]

    async def get_experiment(self, eid):
        self.calls.append(("get_experiment", eid))
        if eid == "missing":
            raise ValueError("Experiment not found")
        return {"id": eid}

    async def create_experiment(
        self,
        org_id,
        name,
        hypothesis="",
        traffic_split=None,
        success_goal_id="",
        created_by="",
    ):
        self.calls.append(("create_experiment", org_id))
        return {"id": "new-exp"}

    async def update_experiment(self, eid, **kw):
        self.calls.append(("update_experiment", eid))
        if eid == "missing":
            raise ValueError("Experiment not found")
        return {"id": eid}

    async def delete_experiment(self, eid):
        self.calls.append(("delete_experiment", eid))
        if eid == "missing":
            raise ValueError("Experiment not found")

    # Variants
    async def list_variants(self, experiment_id):
        self.calls.append(("list_variants", experiment_id))
        return [{"id": "v1"}]

    async def create_variant(
        self, experiment_id, name="", description="", changes=None
    ):
        self.calls.append(("create_variant", experiment_id))
        return {"id": "new-var"}

    async def update_variant_stats(self, vid, impressions=0, conversions=0):
        self.calls.append(("update_variant_stats", vid))
        if vid == "missing":
            raise ValueError("Variant not found")
        return {"id": vid}

    async def delete_variant(self, vid):
        self.calls.append(("delete_variant", vid))

    # Assignment
    async def get_or_assign(self, experiment_id, anonymous_id, variant_id=""):
        self.calls.append(("get_or_assign", experiment_id, anonymous_id))
        return {"experiment_id": experiment_id, "variant_id": variant_id or "v1"}

    # Dashboard
    async def dashboard_event_breakdown(self, org_id, start, end):
        self.calls.append(("dashboard_event_breakdown", org_id))
        return [{"event_category": "pageview", "count": 100}]

    async def dashboard_conversion_summary(self, org_id, start, end):
        self.calls.append(("dashboard_conversion_summary", org_id))
        return [{"goal_name": "Sign Up", "count": 50}]

    async def dashboard_experiment_summary(self, org_id):
        self.calls.append(("dashboard_experiment_summary", org_id))
        return [{"experiment_name": "CTA Color", "status": "running"}]


# ═══════════════════════════════════════════════════════════════
# Test Helpers
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


def _token(sub="u1", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


class AnalyticsClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig = ana_handler.AnalyticsService
        ana_handler.AnalyticsService = lambda env, ctx=None: self.svc
        try:
            return asyncio.run(
                ana_handler.handle_analytics(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            ana_handler.AnalyticsService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None, json_body=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json_body)


@pytest.fixture
def ana_svc():
    return FakeAnalyticsService(type("E", (), {})())


@pytest.fixture
def client(ana_svc):
    return AnalyticsClient(ana_svc)


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Events
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsEventsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, client):
        resp = client.get("/api/analytics/events?org_id=org1")
        assert resp.status_code == 401

    def test_list_events(self, client, ana_svc):
        resp = client.get("/api/analytics/events?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_events_missing_org(self, client, ana_svc):
        resp = client.get("/api/analytics/events", headers=self._h())
        assert resp.status_code == 400

    def test_track_event(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/events",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "event_category": "pageview",
                "event_action": "view",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-evt"


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Goals & Conversions
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsGoalsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_goals(self, client, ana_svc):
        resp = client.get("/api/analytics/goals?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["goals"]) == 1

    def test_list_goals_missing_org(self, client, ana_svc):
        resp = client.get("/api/analytics/goals", headers=self._h())
        assert resp.status_code == 400

    def test_get_goal(self, client, ana_svc):
        resp = client.get("/api/analytics/goals/g1", headers=self._h())
        assert resp.status_code == 200

    def test_get_goal_missing(self, client, ana_svc):
        resp = client.get("/api/analytics/goals/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_goal(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/goals",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Sign Up", "goal_type": "event"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-goal"

    def test_update_goal(self, client, ana_svc):
        resp = client.put(
            "/api/analytics/goals/g1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_update_goal_missing(self, client, ana_svc):
        resp = client.put(
            "/api/analytics/goals/missing",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 400

    def test_delete_goal(self, client, ana_svc):
        resp = client.delete("/api/analytics/goals/g1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_goal_missing(self, client, ana_svc):
        resp = client.delete("/api/analytics/goals/missing", headers=self._h())
        assert resp.status_code == 404

    # Conversions sub-resource
    def test_list_conversions(self, client, ana_svc):
        resp = client.get("/api/analytics/goals/g1/conversions", headers=self._h())
        assert resp.status_code == 200

    def test_record_conversion(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/goals/g1/conversions",
            headers=self._h(),
            json_body={"org_id": "org1", "user_id": "u1", "value_cents": 500},
        )
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Funnels
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsFunnelsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_funnels(self, client, ana_svc):
        resp = client.get("/api/analytics/funnels?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["funnels"]) == 1

    def test_list_funnels_missing_org(self, client, ana_svc):
        resp = client.get("/api/analytics/funnels", headers=self._h())
        assert resp.status_code == 400

    def test_get_funnel(self, client, ana_svc):
        resp = client.get("/api/analytics/funnels/f1", headers=self._h())
        assert resp.status_code == 200

    def test_get_funnel_missing(self, client, ana_svc):
        resp = client.get("/api/analytics/funnels/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_funnel(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/funnels",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "Onboarding"},
        )
        assert resp.status_code == 201

    def test_update_funnel(self, client, ana_svc):
        resp = client.put(
            "/api/analytics/funnels/f1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_funnel(self, client, ana_svc):
        resp = client.delete("/api/analytics/funnels/f1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_funnel_missing(self, client, ana_svc):
        resp = client.delete("/api/analytics/funnels/missing", headers=self._h())
        assert resp.status_code == 404

    # Steps sub-resource
    def test_list_funnel_steps(self, client, ana_svc):
        resp = client.get("/api/analytics/funnels/f1/steps", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["steps"]) == 1

    def test_create_funnel_step(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/funnels/f1/steps",
            headers=self._h(),
            json_body={"step_number": 1, "name": "Sign Up", "event_category": "auth"},
        )
        assert resp.status_code == 201

    def test_delete_funnel_step(self, client, ana_svc):
        resp = client.delete("/api/analytics/funnels/f1/steps/fs1", headers=self._h())
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════
# Handler Tests — A/B Experiments
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsExperimentsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_list_experiments(self, client, ana_svc):
        resp = client.get("/api/analytics/experiments?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["experiments"]) == 1

    def test_list_experiments_missing_org(self, client, ana_svc):
        resp = client.get("/api/analytics/experiments", headers=self._h())
        assert resp.status_code == 400

    def test_get_experiment(self, client, ana_svc):
        resp = client.get("/api/analytics/experiments/exp1", headers=self._h())
        assert resp.status_code == 200

    def test_get_experiment_missing(self, client, ana_svc):
        resp = client.get("/api/analytics/experiments/missing", headers=self._h())
        assert resp.status_code == 404

    def test_create_experiment(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/experiments",
            headers=self._h(),
            json_body={"org_id": "org1", "name": "CTA Color", "hypothesis": "Red wins"},
        )
        assert resp.status_code == 201

    def test_update_experiment(self, client, ana_svc):
        resp = client.put(
            "/api/analytics/experiments/exp1",
            headers=self._h(),
            json_body={"status": "completed"},
        )
        assert resp.status_code == 200

    def test_delete_experiment(self, client, ana_svc):
        resp = client.delete("/api/analytics/experiments/exp1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_experiment_missing(self, client, ana_svc):
        resp = client.delete("/api/analytics/experiments/missing", headers=self._h())
        assert resp.status_code == 404

    # Variants sub-resource
    def test_list_variants(self, client, ana_svc):
        resp = client.get("/api/analytics/experiments/exp1/variants", headers=self._h())
        assert resp.status_code == 200
        assert len(resp.json()["variants"]) == 1

    def test_create_variant(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/experiments/exp1/variants",
            headers=self._h(),
            json_body={"name": "Red", "changes": {"color": "red"}},
        )
        assert resp.status_code == 201

    def test_update_variant_stats(self, client, ana_svc):
        resp = client.put(
            "/api/analytics/experiments/exp1/variants/v1",
            headers=self._h(),
            json_body={"impressions": 200, "conversions": 20},
        )
        assert resp.status_code == 200

    def test_delete_variant(self, client, ana_svc):
        resp = client.delete(
            "/api/analytics/experiments/exp1/variants/v1", headers=self._h()
        )
        assert resp.status_code == 200

    # Assignment
    def test_assign_variant(self, client, ana_svc):
        resp = client.post(
            "/api/analytics/experiments/exp1/assign",
            headers=self._h(),
            json_body={"anonymous_id": "anon1", "variant_id": "v1"},
        )
        assert resp.status_code == 200
        assert resp.json()["variant_id"] == "v1"


# ═══════════════════════════════════════════════════════════════
# Handler Tests — Dashboard (Steps 27-28)
# ═══════════════════════════════════════════════════════════════
class TestAnalyticsDashboardHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_dashboard_event_breakdown(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/events?org_id=org1&start=2026-01-01&end=2026-01-31",
            headers=self._h(),
        )
        assert resp.status_code == 200
        assert len(resp.json()["breakdown"]) == 1

    def test_dashboard_events_missing_org(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/events?start=2026-01-01&end=2026-01-31",
            headers=self._h(),
        )
        assert resp.status_code == 400

    def test_dashboard_events_missing_dates(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/events?org_id=org1",
            headers=self._h(),
        )
        assert resp.status_code == 400

    def test_dashboard_conversion_summary(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/conversions?org_id=org1&start=2026-01-01&end=2026-01-31",
            headers=self._h(),
        )
        assert resp.status_code == 200
        assert len(resp.json()["conversions"]) == 1

    def test_dashboard_conversions_missing_org(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/conversions?start=2026-01-01&end=2026-01-31",
            headers=self._h(),
        )
        assert resp.status_code == 400

    def test_dashboard_experiment_summary(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/experiments?org_id=org1",
            headers=self._h(),
        )
        assert resp.status_code == 200
        assert len(resp.json()["experiments"]) == 1

    def test_dashboard_experiments_missing_org(self, client, ana_svc):
        resp = client.get("/api/analytics/dashboard/experiments", headers=self._h())
        assert resp.status_code == 400

    def test_dashboard_not_found(self, client, ana_svc):
        resp = client.get(
            "/api/analytics/dashboard/unknown?org_id=org1",
            headers=self._h(),
        )
        assert resp.status_code == 404
