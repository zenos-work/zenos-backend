"""Tests for Phase 2 Step 12 — Author Earnings (model + service + handler)."""

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

earnings_models = importlib.import_module("models.earnings.model")
AuthorEarnings = earnings_models.AuthorEarnings
AuthorPayout = earnings_models.AuthorPayout
TipTransaction = earnings_models.TipTransaction
earnings_handler = importlib.import_module("api.earnings.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestEarningsModels:
    def test_author_earnings_from_row(self):
        row = {
            "id": "e1",
            "author_id": "u1",
            "period_type": "monthly",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "total_earnings_cents": 5000,
            "net_earnings_cents": 4500,
            "platform_fee_cents": 500,
            "status": "confirmed",
            "created_at": "2026-02-01",
            "updated_at": "2026-02-01",
            "org_id": None,
            "premium_read_revenue_cents": 3000,
            "tip_revenue_cents": 2000,
            "course_revenue_cents": 0,
            "marketplace_revenue_cents": 0,
            "premium_reads_count": 150,
            "total_read_time_seconds": 9000,
            "articles_contributing": 5,
        }
        e = AuthorEarnings.from_row(row)
        assert e.total_earnings_cents == 5000
        assert e.net_earnings_cents == 4500

    def test_author_payout_to_dict(self):
        p = AuthorPayout(
            id="p1",
            author_id="u1",
            amount_cents=4500,
            currency="USD",
            payout_method="stripe",
            status="completed",
            requested_at="2026-02-01",
            created_at="2026-02-01",
            completed_at="2026-02-03",
        )
        d = p.to_dict()
        assert d["amount_cents"] == 4500
        assert d["status"] == "completed"
        assert "failure_reason" not in d

    def test_tip_to_dict_author_scope(self):
        t = TipTransaction(
            id="t1",
            tipper_id="u2",
            author_id="u1",
            amount_cents=500,
            currency="USD",
            platform_fee_cents=50,
            net_amount_cents=450,
            status="completed",
            created_at="2026-01-15",
            article_id="a1",
            is_anonymous=0,
            message="Great article!",
        )
        d = t.to_dict(scope="author")
        assert d["tipper_id"] == "u2"
        assert d["net_amount_cents"] == 450

    def test_tip_to_dict_anonymous(self):
        t = TipTransaction(
            id="t1",
            tipper_id="u2",
            author_id="u1",
            amount_cents=500,
            currency="USD",
            platform_fee_cents=50,
            net_amount_cents=450,
            status="completed",
            created_at="2026-01-15",
            is_anonymous=1,
        )
        d = t.to_dict(scope="author")
        assert "tipper_id" not in d  # anonymous


# ── Fake Service ──
class FakeEarningsService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def get_earnings(self, author_id, page=1, limit=20):
        self.calls.append(("get_earnings", author_id))
        return {
            "earnings": [],
            "summary": {"total_earnings_cents": 0, "net_earnings_cents": 0},
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
        }

    async def get_payouts(self, author_id, page=1, limit=20):
        self.calls.append(("get_payouts", author_id))
        return {
            "payouts": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
        }

    async def request_payout(
        self,
        author_id,
        amount_cents,
        currency="USD",
        payout_method="stripe",
        period_start=None,
        period_end=None,
    ):
        self.calls.append(("request_payout", author_id, amount_cents))
        if amount_cents <= 0:
            raise ValueError("Amount must be positive")
        if amount_cents == 99999:
            raise ValueError("A pending payout already exists")
        return "new-payout-id"

    async def send_tip(
        self,
        tipper_id,
        author_id,
        amount_cents,
        article_id=None,
        currency="USD",
        message=None,
        is_anonymous=False,
    ):
        self.calls.append(("send_tip", tipper_id, author_id, amount_cents))
        if amount_cents <= 0:
            raise ValueError("Tip amount must be positive")
        if tipper_id == author_id:
            raise ValueError("Cannot tip yourself")
        return "new-tip-id"

    async def get_tips_received(self, author_id, page=1, limit=20):
        self.calls.append(("get_tips_received", author_id))
        return {
            "tips": [],
            "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
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


class EarningsClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

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

        orig = earnings_handler.EarningsService
        earnings_handler.EarningsService = _make_svc
        try:
            return asyncio.run(
                earnings_handler.handle_earnings(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            earnings_handler.EarningsService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeEarningsService(_Env())


@pytest.fixture
def client(svc):
    return EarningsClient(svc)


# ── Handler Tests ──
class TestEarningsHandler:
    def test_get_earnings(self, client, svc):
        resp = client.get(
            "/api/earnings/me",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "earnings" in resp.json()

    def test_get_payouts(self, client, svc):
        resp = client.get(
            "/api/earnings/me/payouts",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "payouts" in resp.json()

    def test_request_payout(self, client, svc):
        resp = client.post(
            "/api/earnings/me/payouts/request",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"amount_cents": 5000, "payout_method": "stripe"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    def test_request_payout_invalid_amount(self, client, svc):
        resp = client.post(
            "/api/earnings/me/payouts/request",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"amount_cents": 0},
        )
        assert resp.status_code == 400

    def test_send_tip(self, client, svc):
        resp = client.post(
            "/api/tips/a1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"author_id": "other-user", "amount_cents": 500},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "completed"

    def test_send_tip_to_self(self, client, svc):
        resp = client.post(
            "/api/tips/a1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"author_id": "auth-user", "amount_cents": 500},
        )
        assert resp.status_code == 400

    def test_get_tips_received(self, client, svc):
        resp = client.get(
            "/api/tips/me/received",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 200
        assert "tips" in resp.json()

    def test_unauth(self, client):
        resp = client.get("/api/earnings/me")
        assert resp.status_code == 401
