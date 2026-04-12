"""Tests for Phase 12 — Financial Engine & Compliance (Step 46 first)."""

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

calc_distribution = importlib.import_module(
    "api.earnings.distribution"
).calculate_distribution
earnings_handler = importlib.import_module("api.earnings.handler")
billing_handler = importlib.import_module("api.billing.handler")
stripe_webhook_mod = importlib.import_module("api.billing.webhook_handler")
compliance_handler = importlib.import_module("api.compliance.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


class _FeatureFlagOn:
    def __init__(self, *_args, **_kwargs):
        pass

    async def evaluate_one(self, *_args, **_kwargs):
        return True


class TestDistributionAlgorithm:
    def test_distribution_splits_by_read_time(self):
        reads = [
            {"reader_id": "r1", "author_id": "a1", "read_time_seconds": 80},
            {"reader_id": "r1", "author_id": "a2", "read_time_seconds": 20},
            {"reader_id": "r2", "author_id": "a1", "read_time_seconds": 50},
            {"reader_id": "r2", "author_id": "a2", "read_time_seconds": 50},
        ]
        out = calc_distribution(
            reads=reads,
            active_subscribers=2,
            payout_ratio=0.70,
            contribution_cents=500,
            min_payout_cents=1,
        )
        # pool = 2 * 500 * 0.70 = 700
        assert out["total_pool_cents"] == 700
        assert out["author_shares"]["a1"] > out["author_shares"]["a2"]
        assert sum(out["author_shares"].values()) in {699, 700, 701}

    def test_distribution_threshold(self):
        reads = [{"reader_id": "r1", "author_id": "a1", "read_time_seconds": 100}]
        out = calc_distribution(
            reads=reads,
            active_subscribers=1,
            payout_ratio=0.70,
            contribution_cents=500,
            min_payout_cents=1000,
        )
        assert "a1" in out["below_threshold"]
        assert out["eligible_payouts"] == {}

    def test_distribution_invalid_args(self):
        with pytest.raises(ValueError):
            calc_distribution([], -1)
        with pytest.raises(ValueError):
            calc_distribution([], 1, payout_ratio=1.5)


class FakeEarningsService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def get_earnings(self, author_id, page=1, limit=20):
        return {
            "earnings": [],
            "summary": {},
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
        }

    async def get_payouts(self, author_id, page=1, limit=20):
        return {
            "payouts": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
        }

    async def request_payout(self, *args, **kwargs):
        return "p1"

    async def send_tip(self, *args, **kwargs):
        return "t1"

    async def get_tips_received(self, author_id, page=1, limit=20):
        return {
            "tips": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
        }

    async def calculate_monthly_distribution(
        self,
        period_start,
        period_end,
        active_subscribers,
        payout_ratio=0.70,
        min_payout_cents=2500,
    ):
        self.calls.append(("calculate", period_start, active_subscribers))
        if active_subscribers < 0:
            raise ValueError("active_subscribers cannot be negative")
        return {
            "period_start": period_start,
            "period_end": period_end,
            "distribution": {
                "total_pool_cents": 700,
                "author_shares": {"a1": 500, "a2": 200},
            },
            "persisted_rows": 2,
            "pending_payouts_created": 0,
        }

    async def distribution_report(self, period_start):
        self.calls.append(("report", period_start))
        return {
            "period_start": period_start,
            "authors": [],
            "authors_count": 0,
            "total_earnings_cents": 0,
        }

    async def my_breakdown(self, author_id, period_start):
        self.calls.append(("breakdown", author_id, period_start))
        return {
            "period_start": period_start,
            "breakdown": [],
            "total_earnings_cents": 0,
        }


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


def _make_client(fake_svc):
    class Client:
        def __init__(self, svc):
            self.svc = svc

        def _dispatch(self, method, path, headers=None, json_body=None):
            parsed = urlparse(path)
            req = FakeRequest(method, path, headers=headers or {}, json_body=json_body)

            class _Env:
                JWT_SECRET = _JWT_SECRET

            orig = earnings_handler.EarningsService
            orig_flags = earnings_handler.FeatureFlagService
            earnings_handler.EarningsService = lambda env, ctx=None: self.svc
            earnings_handler.FeatureFlagService = _FeatureFlagOn
            try:
                return asyncio.run(
                    earnings_handler.handle_earnings(
                        req,
                        _Env(),
                        parsed.path,
                        method,
                        parse_qs(parsed.query),
                        FakeCtx(),
                    )
                )
            finally:
                earnings_handler.EarningsService = orig
                earnings_handler.FeatureFlagService = orig_flags

        def get(self, path, headers=None):
            return self._dispatch("GET", path, headers=headers)

        def post(self, path, headers=None, json_body=None):
            return self._dispatch("POST", path, headers=headers, json_body=json_body)

    return Client(fake_svc)


@pytest.fixture
def svc():
    return FakeEarningsService(type("E", (), {})())


@pytest.fixture
def client(svc):
    return _make_client(svc)


class TestEarningsEndpoints:
    def _h(self, role="AUTHOR"):
        return {"Authorization": f"Bearer {_token(role=role)}"}

    def test_admin_calculate_distribution_superadmin(self, client):
        resp = client.post(
            "/api/admin/earnings/calculate",
            headers=self._h("SUPERADMIN"),
            json_body={
                "period_start": "2026-04-01",
                "period_end": "2026-05-01",
                "active_subscribers": 2,
            },
        )
        assert resp.status_code == 200
        assert "distribution" in resp.json()

    def test_admin_calculate_distribution_forbidden(self, client):
        resp = client.post(
            "/api/admin/earnings/calculate",
            headers=self._h("AUTHOR"),
            json_body={
                "period_start": "2026-04-01",
                "period_end": "2026-05-01",
                "active_subscribers": 2,
            },
        )
        assert resp.status_code == 403

    def test_admin_distribution_report(self, client):
        resp = client.get(
            "/api/admin/earnings/period/2026-04-01",
            headers=self._h("SUPERADMIN"),
        )
        assert resp.status_code == 200
        assert "authors" in resp.json()

    def test_my_breakdown(self, client):
        resp = client.get(
            "/api/earnings/me/breakdown?period_start=2026-04-01",
            headers=self._h(),
        )
        assert resp.status_code == 200
        assert "breakdown" in resp.json()


class FakeStripeWebhookHandler:
    def __init__(self, db, ctx=None):
        self.calls = []

    async def process_event(self, payload, signature_header, secret):
        self.calls.append((payload.get("type"), signature_header))
        if signature_header == "bad":
            raise ValueError("Invalid Stripe signature")
        return {
            "event_id": payload.get("id", "evt_1"),
            "event_type": payload.get("type", "invoice.paid"),
            "status": "processed",
        }


class FakeBillingReconciliation:
    def __init__(self, db, ctx=None):
        self.calls = []

    async def report(self, period):
        self.calls.append(("report", period))
        return {"period": period, "discrepancies": [], "count": 0}

    async def reconcile(self, period, threshold_cents=1000):
        self.calls.append(("reconcile", period, threshold_cents))
        return {
            "period": period,
            "threshold_cents": threshold_cents,
            "discrepancies_found": 0,
            "discrepancies_inserted": 0,
            "ok": True,
        }


def _make_billing_client():
    class Client:
        def _dispatch(self, method, path, headers=None, json_body=None):
            parsed = urlparse(path)
            req = FakeRequest(method, path, headers=headers or {}, json_body=json_body)

            class _Env:
                JWT_SECRET = _JWT_SECRET
                STRIPE_WEBHOOK_SECRET = "whsec_test"
                DB = object()

            orig_webhook = billing_handler.StripeWebhookHandler
            orig_recon = billing_handler.BillingReconciliation
            orig_flags = billing_handler.FeatureFlagService
            billing_handler.StripeWebhookHandler = FakeStripeWebhookHandler
            billing_handler.BillingReconciliation = FakeBillingReconciliation
            billing_handler.FeatureFlagService = _FeatureFlagOn
            try:
                return asyncio.run(
                    billing_handler.handle_billing(
                        req,
                        _Env(),
                        parsed.path,
                        method,
                        parse_qs(parsed.query),
                        FakeCtx(),
                    )
                )
            finally:
                billing_handler.StripeWebhookHandler = orig_webhook
                billing_handler.BillingReconciliation = orig_recon
                billing_handler.FeatureFlagService = orig_flags

        def get(self, path, headers=None):
            return self._dispatch("GET", path, headers=headers)

        def post(self, path, headers=None, json_body=None):
            return self._dispatch("POST", path, headers=headers, json_body=json_body)

    return Client()


class TestBillingEndpoints:
    def _h(self, role="SUPERADMIN"):
        return {"Authorization": f"Bearer {_token(role=role)}"}

    def test_webhook_processed(self):
        c = _make_billing_client()
        resp = c.post(
            "/api/billing/webhooks/stripe",
            headers={"Stripe-Signature": "t=1,v1=ok"},
            json_body={"id": "evt_1", "type": "invoice.paid"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "processed"

    def test_webhook_invalid_signature(self):
        c = _make_billing_client()
        resp = c.post(
            "/api/billing/webhooks/stripe",
            headers={"Stripe-Signature": "bad"},
            json_body={"id": "evt_1", "type": "invoice.paid"},
        )
        assert resp.status_code == 400

    def test_admin_reconciliation_report(self):
        c = _make_billing_client()
        resp = c.get(
            "/api/admin/billing/reconciliation/2026-04",
            headers=self._h("SUPERADMIN"),
        )
        assert resp.status_code == 200
        assert "discrepancies" in resp.json()

    def test_admin_reconcile_requires_period(self):
        c = _make_billing_client()
        resp = c.post(
            "/api/admin/billing/reconcile",
            headers=self._h("SUPERADMIN"),
            json_body={},
        )
        assert resp.status_code == 400

    def test_admin_reconcile_success(self):
        c = _make_billing_client()
        resp = c.post(
            "/api/admin/billing/reconcile",
            headers=self._h("SUPERADMIN"),
            json_body={"period": "2026-04", "threshold_cents": 1000},
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

    def test_admin_billing_forbidden_for_non_superadmin(self):
        c = _make_billing_client()
        resp = c.get(
            "/api/admin/billing/reconciliation/2026-04",
            headers=self._h("AUTHOR"),
        )
        assert resp.status_code == 403


class TestStripeSignatureVerification:
    def test_verify_signature_valid(self):
        handler = stripe_webhook_mod.StripeWebhookHandler(type("DB", (), {})())
        payload = json.dumps(
            {"id": "evt_1", "type": "invoice.paid"},
            separators=(",", ":"),
            sort_keys=True,
        )
        signed = "1." + payload
        import hmac
        import hashlib

        secret = "whsec_test"
        sig = hmac.new(
            secret.encode("utf-8"), signed.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        ok = handler.verify_signature(payload, f"t=1,v1={sig}", secret)
        assert ok is True

    def test_verify_signature_invalid(self):
        handler = stripe_webhook_mod.StripeWebhookHandler(type("DB", (), {})())
        payload = json.dumps(
            {"id": "evt_1", "type": "invoice.paid"},
            separators=(",", ":"),
            sort_keys=True,
        )
        ok = handler.verify_signature(payload, "t=1,v1=deadbeef", "whsec_test")
        assert ok is False


class FakeExportService:
    def __init__(self, db, ctx=None):
        self.calls = []

    async def request_export(self, user_id):
        self.calls.append(("request_export", user_id))
        return "exp1"

    async def get_export(self, user_id, request_id):
        self.calls.append(("get_export", user_id, request_id))
        if request_id == "missing":
            return None
        return {
            "id": request_id,
            "status": "completed",
            "download_url": "https://example.com/file.zip",
            "expires_at": "2026-04-30",
        }


class FakeErasureService:
    def __init__(self, db, ctx=None):
        self.calls = []

    async def request_erasure(self, user_id, password_confirmed):
        self.calls.append(("request_erasure", user_id, password_confirmed))
        if not password_confirmed:
            raise ValueError("password confirmation is required")
        return "er1"

    async def queue(self):
        self.calls.append(("queue",))
        return [{"id": "er1", "user_id": "u1", "status": "pending"}]

    async def execute_erasure(self, request_id, actor_user_id):
        self.calls.append(("execute_erasure", request_id, actor_user_id))
        if request_id == "missing":
            raise ValueError("Erasure request not found")
        return {"id": request_id, "user_id": "u1", "status": "executed"}


def _make_compliance_client():
    class Client:
        def _dispatch(self, method, path, headers=None, json_body=None):
            parsed = urlparse(path)
            req = FakeRequest(method, path, headers=headers or {}, json_body=json_body)

            class _Env:
                JWT_SECRET = _JWT_SECRET
                DB = object()

            orig_export = compliance_handler.ExportService
            orig_erasure = compliance_handler.ErasureService
            orig_flags = compliance_handler.FeatureFlagService
            compliance_handler.ExportService = FakeExportService
            compliance_handler.ErasureService = FakeErasureService
            compliance_handler.FeatureFlagService = _FeatureFlagOn
            try:
                return asyncio.run(
                    compliance_handler.handle_compliance(
                        req,
                        _Env(),
                        parsed.path,
                        method,
                        parse_qs(parsed.query),
                        FakeCtx(),
                    )
                )
            finally:
                compliance_handler.ExportService = orig_export
                compliance_handler.ErasureService = orig_erasure
                compliance_handler.FeatureFlagService = orig_flags

        def get(self, path, headers=None):
            return self._dispatch("GET", path, headers=headers)

        def post(self, path, headers=None, json_body=None):
            return self._dispatch("POST", path, headers=headers, json_body=json_body)

    return Client()


class TestComplianceEndpoints:
    def _h(self, role="AUTHOR"):
        return {"Authorization": f"Bearer {_token(role=role)}"}

    def test_request_data_export(self):
        c = _make_compliance_client()
        resp = c.post("/api/users/me/data-export", headers=self._h())
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    def test_get_data_export(self):
        c = _make_compliance_client()
        resp = c.get("/api/users/me/data-export/exp1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_request_erasure_requires_confirmation(self):
        c = _make_compliance_client()
        resp = c.post(
            "/api/users/me/erase",
            headers=self._h(),
            json_body={"password_confirmed": False},
        )
        assert resp.status_code == 400

    def test_request_erasure_success(self):
        c = _make_compliance_client()
        resp = c.post(
            "/api/users/me/erase",
            headers=self._h(),
            json_body={"password_confirmed": True},
        )
        assert resp.status_code == 201

    def test_admin_erasure_queue(self):
        c = _make_compliance_client()
        resp = c.get(
            "/api/admin/compliance/erasure-queue",
            headers=self._h("SUPERADMIN"),
        )
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_admin_execute_erasure(self):
        c = _make_compliance_client()
        resp = c.post(
            "/api/admin/compliance/erasure/er1/execute",
            headers=self._h("SUPERADMIN"),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "executed"

    def test_admin_compliance_forbidden_for_non_superadmin(self):
        c = _make_compliance_client()
        resp = c.get(
            "/api/admin/compliance/erasure-queue",
            headers=self._h("AUTHOR"),
        )
        assert resp.status_code == 403
