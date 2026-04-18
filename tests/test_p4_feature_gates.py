"""P4 feature gate and SUPERADMIN guard coverage."""

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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

podcasts_handler = importlib.import_module("api.podcasts.handler")
publications_handler = importlib.import_module("api.publications.handler")
marketing_handler = importlib.import_module("api.marketing.handler")
leads_handler = importlib.import_module("api.leads.handler")
referrals_handler = importlib.import_module("api.referrals.handler")
workflow_costs_handler = importlib.import_module("api.workflow_costs.handler")
usage_alerts_handler = importlib.import_module("api.usage_alerts.handler")
earnings_handler = importlib.import_module("api.earnings.handler")
billing_handler = importlib.import_module("api.billing.handler")
compliance_handler = importlib.import_module("api.compliance.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

JWT_SECRET = "test-secret"


class DummyService:
    def __init__(self, *_args, **_kwargs):
        pass


class FeatureFlagOff:
    def __init__(self, *_args, **_kwargs):
        pass

    async def evaluate_one(self, *_args, **_kwargs):
        return False


class FeatureFlagOn:
    def __init__(self, *_args, **_kwargs):
        pass

    async def evaluate_one(self, *_args, **_kwargs):
        return True


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


class Env:
    JWT_SECRET = JWT_SECRET
    DB = object()


def _token(role="AUTHOR", sub="u-1"):
    return create_token({"sub": sub, "role": role}, JWT_SECRET)


def _dispatch(handler_fn, path, method="GET", role="AUTHOR", json_body=None):
    parsed = urlparse(path)
    req = FakeRequest(
        method=method,
        url=path,
        headers={"Authorization": f"Bearer {_token(role=role)}"},
        json_body=json_body,
    )
    return asyncio.run(
        handler_fn(req, Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx())
    )


def _assert_feature_disabled(resp, key):
    assert resp.status_code == 403
    assert key in str(resp.json().get("error", ""))


def test_p4_handlers_reject_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(podcasts_handler, "PodcastService", DummyService)
    monkeypatch.setattr(publications_handler, "PublicationService", DummyService)
    monkeypatch.setattr(marketing_handler, "MarketingService", DummyService)
    monkeypatch.setattr(leads_handler, "LeadService", DummyService)
    monkeypatch.setattr(referrals_handler, "ReferralService", DummyService)
    monkeypatch.setattr(workflow_costs_handler, "WorkflowCostService", DummyService)
    monkeypatch.setattr(usage_alerts_handler, "UsageAlertService", DummyService)

    for module in [
        podcasts_handler,
        publications_handler,
        marketing_handler,
        leads_handler,
        referrals_handler,
        workflow_costs_handler,
        usage_alerts_handler,
    ]:
        monkeypatch.setattr(module, "FeatureFlagService", FeatureFlagOff)

    _assert_feature_disabled(
        _dispatch(podcasts_handler.handle_podcasts, "/api/podcasts"), "podcasts"
    )
    _assert_feature_disabled(
        _dispatch(publications_handler.handle_publications, "/api/publications/issues"),
        "publications",
    )
    _assert_feature_disabled(
        _dispatch(marketing_handler.handle_marketing, "/api/marketing/campaigns"),
        "marketing_tools",
    )
    _assert_feature_disabled(
        _dispatch(leads_handler.handle_leads, "/api/leads/forms?org_id=org-1"), "leads"
    )
    _assert_feature_disabled(
        _dispatch(referrals_handler.handle_referrals, "/api/referrals"), "referrals"
    )
    _assert_feature_disabled(
        _dispatch(
            workflow_costs_handler.handle_workflow_costs,
            "/api/workflow-costs/summaries?org_id=org-1",
        ),
        "workflow_costs",
    )
    _assert_feature_disabled(
        _dispatch(
            usage_alerts_handler.handle_usage_alerts, "/api/usage/alerts?org_id=org-1"
        ),
        "usage_alerts",
    )


def test_admin_endpoints_require_superadmin(monkeypatch):
    monkeypatch.setattr(earnings_handler, "EarningsService", DummyService)
    monkeypatch.setattr(billing_handler, "StripeWebhookHandler", DummyService)
    monkeypatch.setattr(billing_handler, "BillingReconciliation", DummyService)
    monkeypatch.setattr(compliance_handler, "ExportService", DummyService)
    monkeypatch.setattr(compliance_handler, "ErasureService", DummyService)

    monkeypatch.setattr(earnings_handler, "FeatureFlagService", FeatureFlagOn)
    monkeypatch.setattr(billing_handler, "FeatureFlagService", FeatureFlagOn)
    monkeypatch.setattr(compliance_handler, "FeatureFlagService", FeatureFlagOn)

    earnings_resp = _dispatch(
        earnings_handler.handle_earnings,
        "/api/admin/earnings/calculate",
        method="POST",
        role="AUTHOR",
        json_body={
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
            "active_subscribers": 10,
        },
    )
    billing_resp = _dispatch(
        billing_handler.handle_billing,
        "/api/admin/billing/reconciliation/2026-04",
        method="GET",
        role="AUTHOR",
    )
    compliance_resp = _dispatch(
        compliance_handler.handle_compliance,
        "/api/admin/compliance/erasure-queue",
        method="GET",
        role="AUTHOR",
    )

    assert earnings_resp.status_code == 403
    assert billing_resp.status_code == 403
    assert compliance_resp.status_code == 403


def test_admin_endpoints_require_enabled_flag_even_for_superadmin(monkeypatch):
    monkeypatch.setattr(earnings_handler, "EarningsService", DummyService)
    monkeypatch.setattr(billing_handler, "StripeWebhookHandler", DummyService)
    monkeypatch.setattr(billing_handler, "BillingReconciliation", DummyService)
    monkeypatch.setattr(compliance_handler, "ExportService", DummyService)
    monkeypatch.setattr(compliance_handler, "ErasureService", DummyService)

    monkeypatch.setattr(earnings_handler, "FeatureFlagService", FeatureFlagOff)
    monkeypatch.setattr(billing_handler, "FeatureFlagService", FeatureFlagOff)
    monkeypatch.setattr(compliance_handler, "FeatureFlagService", FeatureFlagOff)

    earnings_resp = _dispatch(
        earnings_handler.handle_earnings,
        "/api/admin/earnings/calculate",
        method="POST",
        role="SUPERADMIN",
        json_body={
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
            "active_subscribers": 10,
        },
    )
    billing_resp = _dispatch(
        billing_handler.handle_billing,
        "/api/admin/billing/reconciliation/2026-04",
        method="GET",
        role="SUPERADMIN",
    )
    compliance_resp = _dispatch(
        compliance_handler.handle_compliance,
        "/api/admin/compliance/erasure-queue",
        method="GET",
        role="SUPERADMIN",
    )

    assert earnings_resp.status_code == 403
    assert billing_resp.status_code == 403
    assert compliance_resp.status_code == 403
