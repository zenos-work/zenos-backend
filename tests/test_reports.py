"""Tests for Phase 2 Step 11 — Content Reports (model + service + handler)."""

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

ContentReport = importlib.import_module("models.report.model").ContentReport
report_handler = importlib.import_module("api.reports.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ── Model Tests ──
class TestContentReportModel:
    def test_from_row(self):
        row = {
            "id": "rpt1",
            "reporter_id": "u1",
            "resource_type": "article",
            "resource_id": "a1",
            "reason": "spam",
            "status": "pending",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "org_id": None,
            "detail_text": "It's spam",
            "reviewed_by": None,
            "reviewed_at": None,
            "action_taken": None,
            "action_note": None,
        }
        r = ContentReport.from_row(row)
        assert r.id == "rpt1"
        assert r.reason == "spam"

    def test_to_dict_public(self):
        r = ContentReport(
            id="rpt1",
            reporter_id="u1",
            resource_type="article",
            resource_id="a1",
            reason="spam",
            status="pending",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )
        d = r.to_dict(scope="public")
        assert "reviewed_by" not in d

    def test_to_dict_admin(self):
        r = ContentReport(
            id="rpt1",
            reporter_id="u1",
            resource_type="comment",
            resource_id="c1",
            reason="harassment",
            status="actioned",
            created_at="2026-01-01",
            updated_at="2026-01-02",
            reviewed_by="admin1",
            reviewed_at="2026-01-02",
            action_taken="content_removed",
            action_note="Removed",
        )
        d = r.to_dict(scope="admin")
        assert d["reviewed_by"] == "admin1"
        assert d["action_taken"] == "content_removed"


# ── Fake Service ──
class FakeReportService:
    def __init__(self, env, ctx=None):
        self.calls = []
        self._repo = type(
            "FakeRepo",
            (),
            {
                "find_by_id": self._find_by_id,
            },
        )()

    async def _find_by_id(self, report_id):
        if report_id == "missing":
            return None
        return ContentReport(
            id=report_id,
            reporter_id="u1",
            resource_type="article",
            resource_id="a1",
            reason="spam",
            status="pending",
            created_at="2026-01-01",
            updated_at="2026-01-01",
        )

    async def submit_report(
        self,
        reporter_id,
        resource_type,
        resource_id,
        reason,
        org_id=None,
        detail_text=None,
    ):
        self.calls.append(
            ("submit_report", reporter_id, resource_type, resource_id, reason)
        )
        if resource_type not in {"article", "comment", "user"}:
            raise ValueError(f"Invalid resource_type: {resource_type}")
        if reason not in {"spam", "harassment"}:
            raise ValueError(f"Invalid reason: {reason}")
        if resource_id == "dup":
            raise ValueError("You have already reported this resource")
        return "new-report-id"

    async def list_reports(self, status=None, page=1, limit=20):
        self.calls.append(("list_reports", status))
        return {
            "reports": [{"id": "rpt1", "status": "pending"}],
            "pagination": {"page": page, "limit": limit, "total": 1, "pages": 1},
        }

    async def review_report(
        self, report_id, reviewer_id, status, action_taken=None, action_note=None
    ):
        self.calls.append(("review_report", report_id, status))
        if report_id == "missing":
            raise ValueError("Report not found")
        if status == "invalid_status":
            raise ValueError(f"Invalid status: {status}")
        return {"id": report_id, "status": status}


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


class ReportClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json=None):
        return self._dispatch("POST", path, headers=headers, json_body=json)

    def put(self, path, headers=None, json=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json)

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

        orig = report_handler.ReportService
        report_handler.ReportService = _make_svc
        try:
            return asyncio.run(
                report_handler.handle_reports(
                    req, _Env(), parsed.path, method, parse_qs(parsed.query), FakeCtx()
                )
            )
        finally:
            report_handler.ReportService = orig


def _token(sub="auth-user", role="AUTHOR"):
    return create_token({"sub": sub, "role": role}, _JWT_SECRET)


def _admin_token():
    return create_token({"sub": "approver-user", "role": "APPROVER"}, _JWT_SECRET)


@pytest.fixture
def svc():
    class _Env:
        pass

    return FakeReportService(_Env())


@pytest.fixture
def client(svc):
    return ReportClient(svc)


# ── Handler Tests ──
class TestReportHandler:
    def test_submit_report(self, client, svc):
        resp = client.post(
            "/api/reports",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"resource_type": "article", "resource_id": "a1", "reason": "spam"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

    def test_submit_invalid_reason(self, client, svc):
        resp = client.post(
            "/api/reports",
            headers={"Authorization": f"Bearer {_token()}"},
            json={
                "resource_type": "article",
                "resource_id": "a1",
                "reason": "bad_reason",
            },
        )
        assert resp.status_code == 400

    def test_submit_duplicate(self, client, svc):
        resp = client.post(
            "/api/reports",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"resource_type": "article", "resource_id": "dup", "reason": "spam"},
        )
        assert resp.status_code == 400

    def test_list_reports_admin(self, client, svc):
        resp = client.get(
            "/api/admin/reports",
            headers={"Authorization": f"Bearer {_admin_token()}"},
        )
        assert resp.status_code == 200
        assert "reports" in resp.json()

    def test_list_reports_non_admin(self, client, svc):
        resp = client.get(
            "/api/admin/reports",
            headers={"Authorization": f"Bearer {_token()}"},
        )
        assert resp.status_code == 403

    def test_review_report_admin(self, client, svc):
        resp = client.put(
            "/api/admin/reports/rpt1",
            headers={"Authorization": f"Bearer {_admin_token()}"},
            json={"status": "actioned", "action_taken": "content_removed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "actioned"

    def test_review_report_non_admin(self, client, svc):
        resp = client.put(
            "/api/admin/reports/rpt1",
            headers={"Authorization": f"Bearer {_token()}"},
            json={"status": "actioned"},
        )
        assert resp.status_code == 403

    def test_unauth(self, client):
        resp = client.post("/api/reports", json={"resource_type": "article"})
        assert resp.status_code == 401
