"""Tests for Phase 10 — Notification Prefs, Workflow Costs, Usage Alerts (model + handler)."""

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
np_models = importlib.import_module("models.notification_pref.model")
NotificationPreference = np_models.NotificationPreference
PushSubscription = np_models.PushSubscription

wc_models = importlib.import_module("models.workflow_cost.model")
WorkflowNodeCostRate = wc_models.WorkflowNodeCostRate
WorkflowRunCost = wc_models.WorkflowRunCost
WorkflowCostSummary = wc_models.WorkflowCostSummary
OrgCostMonthlyRollup = wc_models.OrgCostMonthlyRollup

ar_models = importlib.import_module("models.alert_rule.model")
AlertRule = ar_models.AlertRule

np_handler = importlib.import_module("api.notification_prefs.handler")
wc_handler = importlib.import_module("api.workflow_costs.handler")
ua_handler = importlib.import_module("api.usage_alerts.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Notification Pref Model Tests
# ═══════════════════════════════════════════════════════════════
class TestNotificationPrefModels:
    def test_pref_from_row(self):
        row = {
            "user_id": "u1",
            "notification_type": "comment",
            "channel": "email",
            "is_enabled": 1,
        }
        p = NotificationPreference.from_row(row)
        assert p.notification_type == "comment"
        assert p.channel == "email"
        assert p.is_enabled is True

    def test_pref_from_row_none(self):
        assert NotificationPreference.from_row(None) is None

    def test_pref_to_dict(self):
        p = NotificationPreference(user_id="u1", notification_type="like")
        d = p.to_dict()
        assert d["user_id"] == "u1"
        assert d["is_enabled"] is True

    def test_pref_disabled(self):
        row = {
            "user_id": "u1",
            "notification_type": "comment",
            "channel": "push",
            "is_enabled": 0,
        }
        p = NotificationPreference.from_row(row)
        assert p.is_enabled is False

    def test_push_sub_from_row(self):
        row = {
            "id": "ps1",
            "user_id": "u1",
            "platform": "web",
            "endpoint": "https://push.example.com/sub1",
            "p256dh_key": "key1",
            "auth_key": "auth1",
            "device_name": "Chrome",
            "is_active": 1,
            "created_at": "2026-01-01",
            "last_used_at": "",
        }
        s = PushSubscription.from_row(row)
        assert s.endpoint == "https://push.example.com/sub1"
        assert s.is_active is True

    def test_push_sub_from_row_none(self):
        assert PushSubscription.from_row(None) is None

    def test_push_sub_to_dict_default(self):
        s = PushSubscription(id="ps1", p256dh_key="secret", auth_key="auth")
        d = s.to_dict()
        assert "p256dh_key" not in d
        assert "auth_key" not in d

    def test_push_sub_to_dict_admin(self):
        s = PushSubscription(id="ps1", p256dh_key="secret", auth_key="auth")
        d = s.to_dict(scope="admin")
        assert d["p256dh_key"] == "secret"
        assert d["auth_key"] == "auth"


# ═══════════════════════════════════════════════════════════════
# Workflow Cost Model Tests
# ═══════════════════════════════════════════════════════════════
class TestWorkflowCostModels:
    def test_rate_from_row(self):
        row = {
            "id": "r1",
            "org_id": "org1",
            "node_type_id": "llm",
            "cost_model": "per_token",
            "rate_microcents": 150,
            "unit_label": "1k tokens",
            "currency": "USD",
            "notes": "GPT-4",
            "created_at": "2026-01-01",
        }
        r = WorkflowNodeCostRate.from_row(row)
        assert r.node_type_id == "llm"
        assert r.rate_microcents == 150
        assert r.cost_model == "per_token"

    def test_rate_from_row_none(self):
        assert WorkflowNodeCostRate.from_row(None) is None

    def test_rate_to_dict(self):
        r = WorkflowNodeCostRate(id="r1", node_type_id="llm")
        d = r.to_dict()
        assert d["node_type_id"] == "llm"

    def test_run_cost_from_row(self):
        row = {
            "id": "c1",
            "run_id": "run1",
            "step_id": "step1",
            "workflow_id": "wf1",
            "org_id": "org1",
            "node_type_id": "llm",
            "cost_model": "per_token",
            "units_consumed": 1.5,
            "unit_label": "1k tokens",
            "cost_microcents": 225,
            "cost_actual_microcents": 200,
            "currency": "USD",
            "external_ref": "ref1",
            "notes": "",
            "created_at": "2026-01-01",
        }
        c = WorkflowRunCost.from_row(row)
        assert c.units_consumed == 1.5
        assert c.cost_microcents == 225

    def test_run_cost_from_row_none(self):
        assert WorkflowRunCost.from_row(None) is None

    def test_summary_from_row(self):
        row = {
            "workflow_id": "wf1",
            "org_id": "org1",
            "total_runs_costed": 50,
            "total_cost_microcents": 100000,
            "total_ad_spend_microcents": 20000,
            "total_ai_cost_microcents": 60000,
            "total_email_cost_microcents": 20000,
            "last_run_cost_microcents": 2000,
            "avg_run_cost_microcents": 2000,
            "currency": "USD",
            "updated_at": "2026-01-01",
        }
        s = WorkflowCostSummary.from_row(row)
        assert s.total_runs_costed == 50
        assert s.total_cost_microcents == 100000

    def test_summary_from_row_none(self):
        assert WorkflowCostSummary.from_row(None) is None

    def test_monthly_from_row(self):
        row = {
            "id": "m1",
            "org_id": "org1",
            "year_month": "2026-01",
            "workflow_runs": 100,
            "total_cost_microcents": 500000,
            "ad_spend_microcents": 100000,
            "ai_cost_microcents": 300000,
            "email_cost_microcents": 100000,
            "other_cost_microcents": 0,
            "budget_cap_microcents": 1000000,
            "updated_at": "2026-01-31",
        }
        m = OrgCostMonthlyRollup.from_row(row)
        assert m.year_month == "2026-01"
        assert m.budget_cap_microcents == 1000000

    def test_monthly_from_row_none(self):
        assert OrgCostMonthlyRollup.from_row(None) is None

    def test_monthly_to_dict(self):
        m = OrgCostMonthlyRollup(id="m1", org_id="org1", year_month="2026-01")
        d = m.to_dict()
        assert d["year_month"] == "2026-01"
        assert d["budget_cap_microcents"] == 0


# ═══════════════════════════════════════════════════════════════
# Alert Rule Model Tests
# ═══════════════════════════════════════════════════════════════
class TestAlertRuleModel:
    def test_alert_from_row(self):
        row = {
            "id": "ar1",
            "org_id": "org1",
            "created_by": "u1",
            "name": "Cost Spike",
            "alert_type": "cost_spike",
            "config": '{"window":"1h"}',
            "threshold_value": 5000,
            "comparison": "gte",
            "notify_channels": '["email","slack"]',
            "notify_user_ids": '["u1","u2"]',
            "cooldown_minutes": 30,
            "is_active": 1,
            "last_triggered_at": "",
            "trigger_count": 3,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        a = AlertRule.from_row(row)
        assert a.name == "Cost Spike"
        assert a.config == {"window": "1h"}
        assert a.notify_channels == ["email", "slack"]
        assert a.cooldown_minutes == 30
        assert a.trigger_count == 3

    def test_alert_from_row_none(self):
        assert AlertRule.from_row(None) is None

    def test_alert_to_dict(self):
        a = AlertRule(id="ar1", name="Test")
        d = a.to_dict()
        assert d["id"] == "ar1"
        assert d["config"] == {}
        assert d["notify_channels"] == ["in_app"]

    def test_alert_defaults(self):
        a = AlertRule()
        assert a.config == {}
        assert a.notify_channels == ["in_app"]
        assert a.notify_user_ids == []
        assert a.is_active is True


# ═══════════════════════════════════════════════════════════════
# Fake Notification Pref Service
# ═══════════════════════════════════════════════════════════════
class FakeNotificationPrefService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_prefs(self, user_id):
        self.calls.append(("list_prefs", user_id))
        return [
            {"notification_type": "comment", "channel": "email", "is_enabled": True}
        ]

    async def upsert_pref(self, user_id, notification_type, channel, is_enabled=True):
        self.calls.append(("upsert_pref",))
        return {
            "notification_type": notification_type,
            "channel": channel,
            "is_enabled": is_enabled,
        }

    async def bulk_upsert_prefs(self, user_id, prefs):
        self.calls.append(("bulk_upsert_prefs", len(prefs)))
        return prefs

    async def list_push_subs(self, user_id):
        self.calls.append(("list_push_subs", user_id))
        return [{"id": "ps1", "platform": "web"}]

    async def subscribe(
        self, user_id, platform, endpoint, p256dh_key, auth_key, device_name=""
    ):
        self.calls.append(("subscribe",))
        return {"id": "new-push"}

    async def unsubscribe(self, sid):
        self.calls.append(("unsubscribe", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid, "deactivated": True}


# ═══════════════════════════════════════════════════════════════
# Fake Workflow Cost Service
# ═══════════════════════════════════════════════════════════════
class FakeWorkflowCostService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_rates(self, org_id):
        self.calls.append(("list_rates", org_id))
        return [{"id": "r1"}]

    async def list_global_rates(self):
        self.calls.append(("list_global_rates",))
        return [{"id": "r1"}]

    async def create_rate(
        self,
        org_id,
        node_type_id,
        cost_model="per_execution",
        rate_microcents=0,
        unit_label="",
        currency="USD",
        notes="",
    ):
        self.calls.append(("create_rate",))
        return {"id": "new-rate"}

    async def update_rate(self, rid, **kw):
        self.calls.append(("update_rate", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    async def delete_rate(self, rid):
        self.calls.append(("delete_rate", rid))
        if rid == "missing":
            raise ValueError("Not found")

    async def list_run_costs(self, run_id):
        self.calls.append(("list_run_costs", run_id))
        return [{"id": "c1"}]

    async def list_workflow_costs(self, workflow_id, page=1, limit=20):
        self.calls.append(("list_workflow_costs", workflow_id))
        return {"costs": [{"id": "c1"}], "page": page, "limit": limit}

    async def record_cost(
        self,
        run_id,
        step_id,
        workflow_id,
        org_id,
        node_type_id,
        cost_model,
        units_consumed=0,
        unit_label="",
        cost_microcents=0,
        cost_actual_microcents=0,
        currency="USD",
        external_ref="",
        notes="",
    ):
        self.calls.append(("record_cost",))
        return {"id": "new-cost"}

    async def get_cost_summary(self, workflow_id):
        self.calls.append(("get_cost_summary", workflow_id))
        if workflow_id == "missing":
            raise ValueError("Not found")
        return {"workflow_id": workflow_id, "total_cost_microcents": 5000}

    async def list_cost_summaries(self, org_id):
        self.calls.append(("list_cost_summaries", org_id))
        return [{"workflow_id": "wf1"}]

    async def get_monthly_rollup(self, org_id, year_month):
        self.calls.append(("get_monthly_rollup", org_id, year_month))
        if year_month == "missing":
            raise ValueError("Not found")
        return {"org_id": org_id, "year_month": year_month}

    async def list_monthly_rollups(self, org_id, page=1, limit=12):
        self.calls.append(("list_monthly_rollups", org_id))
        return {"rollups": [{"year_month": "2026-01"}], "page": page, "limit": limit}

    async def set_budget_cap(self, org_id, year_month, budget_cap_microcents):
        self.calls.append(("set_budget_cap",))
        return {
            "org_id": org_id,
            "year_month": year_month,
            "budget_cap_microcents": budget_cap_microcents,
        }

    async def check_budget(self, org_id, year_month):
        self.calls.append(("check_budget", org_id))
        return {"exceeded": False}


# ═══════════════════════════════════════════════════════════════
# Fake Usage Alert Service
# ═══════════════════════════════════════════════════════════════
class FakeUsageAlertService:
    def __init__(self, env, ctx=None):
        self.calls = []
        self._quota_exceeded = False

    async def check_quota(self, org_id, year_month):
        self.calls.append(("check_quota", org_id))
        return {
            "org_id": org_id,
            "exceeded": self._quota_exceeded,
            "limit": 100,
            "used": 50,
        }

    async def export_usage_csv(self, org_id):
        self.calls.append(("export_usage_csv", org_id))
        return [{"workflow_id": "wf1", "total_cost_microcents": 5000}]

    async def list_alert_rules(self, org_id):
        self.calls.append(("list_alert_rules", org_id))
        return [{"id": "ar1"}]

    async def get_alert_rule(self, rid):
        self.calls.append(("get_alert_rule", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    async def create_alert_rule(
        self,
        org_id,
        created_by,
        name,
        alert_type,
        config=None,
        threshold_value=0,
        comparison="gte",
        notify_channels=None,
        notify_user_ids=None,
        cooldown_minutes=60,
        is_active=True,
    ):
        self.calls.append(("create_alert_rule",))
        return {"id": "new-rule"}

    async def update_alert_rule(self, rid, **kw):
        self.calls.append(("update_alert_rule", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    async def delete_alert_rule(self, rid):
        self.calls.append(("delete_alert_rule", rid))
        if rid == "missing":
            raise ValueError("Not found")

    async def toggle_alert_rule(self, rid):
        self.calls.append(("toggle_alert_rule", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid, "is_active": False}


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


# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture
def np_svc():
    return FakeNotificationPrefService(type("E", (), {})())


@pytest.fixture
def np_client(np_svc):
    return _make_client(
        np_handler, "handle_notification_prefs", "NotificationPrefService", np_svc
    )


@pytest.fixture
def wc_svc():
    return FakeWorkflowCostService(type("E", (), {})())


@pytest.fixture
def wc_client(wc_svc):
    return _make_client(
        wc_handler, "handle_workflow_costs", "WorkflowCostService", wc_svc
    )


@pytest.fixture
def ua_svc():
    return FakeUsageAlertService(type("E", (), {})())


@pytest.fixture
def ua_client(ua_svc):
    return _make_client(ua_handler, "handle_usage_alerts", "UsageAlertService", ua_svc)


# ═══════════════════════════════════════════════════════════════
# Notification Prefs Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestNotificationPrefsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, np_client):
        resp = np_client.get("/api/notification-prefs")
        assert resp.status_code == 401

    def test_list_prefs(self, np_client):
        resp = np_client.get("/api/notification-prefs", headers=self._h())
        assert resp.status_code == 200
        assert "preferences" in resp.json()

    def test_upsert_pref(self, np_client):
        resp = np_client.post(
            "/api/notification-prefs",
            headers=self._h(),
            json_body={"notification_type": "comment", "channel": "email"},
        )
        assert resp.status_code == 201

    def test_bulk_upsert(self, np_client):
        resp = np_client.put(
            "/api/notification-prefs",
            headers=self._h(),
            json_body={
                "preferences": [
                    {"notification_type": "comment", "channel": "email"},
                    {"notification_type": "like", "channel": "push"},
                ]
            },
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2

    # Push subscriptions
    def test_list_push_subs(self, np_client):
        resp = np_client.get("/api/notification-prefs/push", headers=self._h())
        assert resp.status_code == 200
        assert "subscriptions" in resp.json()

    def test_subscribe_push(self, np_client):
        resp = np_client.post(
            "/api/notification-prefs/push",
            headers=self._h(),
            json_body={
                "endpoint": "https://push.example.com/sub1",
                "p256dh_key": "key1",
                "auth_key": "auth1",
            },
        )
        assert resp.status_code == 201

    def test_unsubscribe_push(self, np_client):
        resp = np_client.delete("/api/notification-prefs/push/ps1", headers=self._h())
        assert resp.status_code == 200

    def test_unsubscribe_push_missing(self, np_client):
        resp = np_client.delete(
            "/api/notification-prefs/push/missing", headers=self._h()
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Workflow Cost Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestWorkflowCostHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/rates")
        assert resp.status_code == 401

    # Rates
    def test_list_rates_global(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/rates", headers=self._h())
        assert resp.status_code == 200
        assert "rates" in resp.json()

    def test_list_rates_by_org(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/rates?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_create_rate(self, wc_client):
        resp = wc_client.post(
            "/api/workflow-costs/rates",
            headers=self._h(),
            json_body={"node_type_id": "llm", "rate_microcents": 150},
        )
        assert resp.status_code == 201

    def test_update_rate(self, wc_client):
        resp = wc_client.put(
            "/api/workflow-costs/rates/r1",
            headers=self._h(),
            json_body={"rate_microcents": 200},
        )
        assert resp.status_code == 200

    def test_update_rate_missing(self, wc_client):
        resp = wc_client.put(
            "/api/workflow-costs/rates/missing",
            headers=self._h(),
            json_body={"rate_microcents": 200},
        )
        assert resp.status_code == 404

    def test_delete_rate(self, wc_client):
        resp = wc_client.delete("/api/workflow-costs/rates/r1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_rate_missing(self, wc_client):
        resp = wc_client.delete("/api/workflow-costs/rates/missing", headers=self._h())
        assert resp.status_code == 404

    # Run costs
    def test_list_run_costs(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/runs/run1", headers=self._h())
        assert resp.status_code == 200
        assert "costs" in resp.json()

    # Workflow costs
    def test_list_workflow_costs(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/workflows/wf1", headers=self._h())
        assert resp.status_code == 200

    # Record cost
    def test_record_cost(self, wc_client):
        resp = wc_client.post(
            "/api/workflow-costs",
            headers=self._h(),
            json_body={
                "run_id": "run1",
                "workflow_id": "wf1",
                "node_type_id": "llm",
                "cost_microcents": 100,
            },
        )
        assert resp.status_code == 201

    # Summaries
    def test_list_summaries(self, wc_client):
        resp = wc_client.get(
            "/api/workflow-costs/summaries?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_get_summary(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/summary/wf1", headers=self._h())
        assert resp.status_code == 200

    def test_get_summary_missing(self, wc_client):
        resp = wc_client.get("/api/workflow-costs/summary/missing", headers=self._h())
        assert resp.status_code == 404

    # Monthly rollups
    def test_list_monthly(self, wc_client):
        resp = wc_client.get(
            "/api/workflow-costs/monthly?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_get_monthly(self, wc_client):
        resp = wc_client.get(
            "/api/workflow-costs/monthly/2026-01?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_get_monthly_missing(self, wc_client):
        resp = wc_client.get(
            "/api/workflow-costs/monthly/missing?org_id=org1", headers=self._h()
        )
        assert resp.status_code == 404

    # Budget
    def test_set_budget_cap(self, wc_client):
        resp = wc_client.put(
            "/api/workflow-costs/budget-cap",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "year_month": "2026-01",
                "budget_cap_microcents": 1000000,
            },
        )
        assert resp.status_code == 200

    def test_check_budget(self, wc_client):
        resp = wc_client.get(
            "/api/workflow-costs/budget-check?org_id=org1&year_month=2026-01",
            headers=self._h(),
        )
        assert resp.status_code == 200
        assert resp.json()["exceeded"] is False


# ═══════════════════════════════════════════════════════════════
# Usage Alerts Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestUsageAlertsHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, ua_client):
        resp = ua_client.get("/api/usage/quota?org_id=org1")
        assert resp.status_code == 401

    # Quota
    def test_check_quota(self, ua_client):
        resp = ua_client.get(
            "/api/usage/quota?org_id=org1&year_month=2026-01", headers=self._h()
        )
        assert resp.status_code == 200
        assert resp.json()["exceeded"] is False

    def test_check_quota_exceeded(self, ua_client, ua_svc):
        ua_svc._quota_exceeded = True
        resp = ua_client.get(
            "/api/usage/quota?org_id=org1&year_month=2026-01", headers=self._h()
        )
        assert resp.status_code == 429

    # Export
    def test_export_usage(self, ua_client):
        resp = ua_client.get("/api/usage/export?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["count"] == 1

    # Alert rules CRUD
    def test_list_alert_rules(self, ua_client):
        resp = ua_client.get("/api/usage/alerts?org_id=org1", headers=self._h())
        assert resp.status_code == 200
        assert "rules" in resp.json()

    def test_create_alert_rule(self, ua_client):
        resp = ua_client.post(
            "/api/usage/alerts",
            headers=self._h(),
            json_body={
                "org_id": "org1",
                "name": "Cost Alert",
                "alert_type": "cost_spike",
            },
        )
        assert resp.status_code == 201

    def test_get_alert_rule(self, ua_client):
        resp = ua_client.get("/api/usage/alerts/ar1", headers=self._h())
        assert resp.status_code == 200

    def test_get_alert_rule_missing(self, ua_client):
        resp = ua_client.get("/api/usage/alerts/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_alert_rule(self, ua_client):
        resp = ua_client.put(
            "/api/usage/alerts/ar1", headers=self._h(), json_body={"name": "Updated"}
        )
        assert resp.status_code == 200

    def test_update_alert_rule_missing(self, ua_client):
        resp = ua_client.put(
            "/api/usage/alerts/missing",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 404

    def test_delete_alert_rule(self, ua_client):
        resp = ua_client.delete("/api/usage/alerts/ar1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_alert_rule_missing(self, ua_client):
        resp = ua_client.delete("/api/usage/alerts/missing", headers=self._h())
        assert resp.status_code == 404

    # Toggle
    def test_toggle_alert_rule(self, ua_client):
        resp = ua_client.post("/api/usage/alerts/ar1/toggle", headers=self._h())
        assert resp.status_code == 200

    def test_toggle_alert_rule_missing(self, ua_client):
        resp = ua_client.post("/api/usage/alerts/missing/toggle", headers=self._h())
        assert resp.status_code == 404
