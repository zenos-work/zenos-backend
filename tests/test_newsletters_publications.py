"""Tests for Phase 7 — Newsletters & Publications (model + handler)."""

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
nl_models = importlib.import_module("models.newsletter.model")
Newsletter = nl_models.Newsletter
NewsletterSubscriber = nl_models.NewsletterSubscriber
NewsletterIssue = nl_models.NewsletterIssue
NewsletterIssueArticle = nl_models.NewsletterIssueArticle
NewsletterSendEvent = nl_models.NewsletterSendEvent
NewsletterSegment = nl_models.NewsletterSegment

pub_models = importlib.import_module("models.publication.model")
NewsletterSubscription = pub_models.NewsletterSubscription
PublicationIssue = pub_models.PublicationIssue
PublicationIssueItem = pub_models.PublicationIssueItem
PublicationGenerationRun = pub_models.PublicationGenerationRun
PublicationDelivery = pub_models.PublicationDelivery

nl_handler = importlib.import_module("api.newsletters.handler")
pub_handler = importlib.import_module("api.publications.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Newsletter Model Tests
# ═══════════════════════════════════════════════════════════════
class TestNewsletterModels:
    def test_newsletter_from_row(self):
        row = {
            "id": "n1",
            "org_id": "org1",
            "owner_id": "u1",
            "name": "Weekly Digest",
            "slug": "weekly-digest",
            "description": "A weekly digest",
            "logo_url": "",
            "cover_url": "",
            "from_name": "Team",
            "from_email": "team@test.com",
            "reply_to_email": "",
            "esp_integration_id": "",
            "is_premium_only": 0,
            "membership_tier": "",
            "status": "active",
            "subscriber_count": 100,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        n = Newsletter.from_row(row)
        assert n.name == "Weekly Digest"
        assert n.subscriber_count == 100
        assert n.is_premium_only is False

    def test_newsletter_from_row_none(self):
        assert Newsletter.from_row(None) is None

    def test_newsletter_to_dict(self):
        n = Newsletter(id="n1", name="Test", slug="test")
        d = n.to_dict()
        assert d["id"] == "n1"
        assert d["name"] == "Test"

    def test_subscriber_from_row(self):
        row = {
            "id": "s1",
            "newsletter_id": "n1",
            "email": "a@b.com",
            "first_name": "A",
            "last_name": "B",
            "lead_id": "",
            "user_id": "",
            "status": "confirmed",
            "consent_at": "",
            "confirmation_token": "tok",
            "confirmed_at": "2026-01-01",
            "open_count": 5,
            "click_count": 2,
            "last_opened_at": "",
            "last_clicked_at": "",
            "subscribed_at": "2026-01-01",
            "unsubscribed_at": "",
            "source": "web",
        }
        s = NewsletterSubscriber.from_row(row)
        assert s.email == "a@b.com"
        assert s.status == "confirmed"
        assert s.open_count == 5

    def test_subscriber_from_row_none(self):
        assert NewsletterSubscriber.from_row(None) is None

    def test_issue_from_row(self):
        row = {
            "id": "i1",
            "newsletter_id": "n1",
            "subject": "Issue #1",
            "preview_text": "",
            "body_html": "<p>Hello</p>",
            "body_text": "Hello",
            "issue_type": "digest",
            "article_ids": '["a1","a2"]',
            "status": "draft",
            "scheduled_at": "",
            "sent_at": "",
            "send_count": 0,
            "open_count": 0,
            "unique_opens": 0,
            "click_count": 0,
            "unique_clicks": 0,
            "unsub_count": 0,
            "bounce_count": 0,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        i = NewsletterIssue.from_row(row)
        assert i.subject == "Issue #1"
        assert i.article_ids == ["a1", "a2"]
        assert i.issue_type == "digest"

    def test_issue_from_row_none(self):
        assert NewsletterIssue.from_row(None) is None

    def test_issue_article_from_row(self):
        row = {
            "issue_id": "i1",
            "article_id": "a1",
            "sort_order": 0,
            "blurb": "Featured",
        }
        ia = NewsletterIssueArticle.from_row(row)
        assert ia.issue_id == "i1"
        assert ia.blurb == "Featured"

    def test_send_event_from_row(self):
        row = {
            "id": "se1",
            "issue_id": "i1",
            "subscriber_id": "s1",
            "event_type": "open",
            "link_url": "",
            "metadata": '{"ua":"chrome"}',
            "created_at": "2026-01-01",
        }
        se = NewsletterSendEvent.from_row(row)
        assert se.event_type == "open"
        assert se.metadata == {"ua": "chrome"}

    def test_segment_from_row(self):
        row = {
            "id": "seg1",
            "newsletter_id": "n1",
            "name": "Active",
            "filter_rules": '{"min_opens":5}',
            "created_at": "2026-01-01",
        }
        seg = NewsletterSegment.from_row(row)
        assert seg.name == "Active"
        assert seg.filter_rules == {"min_opens": 5}


# ═══════════════════════════════════════════════════════════════
# Publication Model Tests
# ═══════════════════════════════════════════════════════════════
class TestPublicationModels:
    def test_subscription_from_row(self):
        row = {
            "id": "sub1",
            "email": "a@b.com",
            "status": "subscribed",
            "source": "web",
            "confirmed_at": "",
            "unsubscribed_at": "",
            "metadata_json": '{"ref":"google"}',
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = NewsletterSubscription.from_row(row)
        assert s.email == "a@b.com"
        assert s.metadata_json == {"ref": "google"}

    def test_subscription_from_row_none(self):
        assert NewsletterSubscription.from_row(None) is None

    def test_pub_issue_from_row(self):
        row = {
            "id": "pi1",
            "issue_type": "magazine",
            "title": "Jan Issue",
            "slug": "jan-issue",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "status": "draft",
            "editorial_preface": "Welcome",
            "toc_json": '{"items":[]}',
            "cover_article_id": "a1",
            "total_pages": 24,
            "pdf_r2_key": "key1",
            "pdf_url": "https://...",
            "metadata_json": "{}",
            "created_by_user_id": "u1",
            "approved_by_user_id": "",
            "approved_at": "",
            "published_at": "",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        pi = PublicationIssue.from_row(row)
        assert pi.title == "Jan Issue"
        assert pi.toc_json == {"items": []}
        assert pi.total_pages == 24

    def test_pub_issue_from_row_none(self):
        assert PublicationIssue.from_row(None) is None

    def test_pub_issue_to_dict_admin(self):
        pi = PublicationIssue(
            id="pi1", title="T", cover_article_id="a1", pdf_r2_key="k1"
        )
        d = pi.to_dict(scope="admin")
        assert d["cover_article_id"] == "a1"
        assert d["pdf_r2_key"] == "k1"

    def test_pub_item_from_row(self):
        row = {
            "id": "it1",
            "issue_id": "pi1",
            "article_id": "a1",
            "section": "features",
            "position": 0,
            "item_type": "article",
            "title": "Feature",
            "excerpt": "...",
            "include_full_content": 1,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        it = PublicationIssueItem.from_row(row)
        assert it.section == "features"
        assert it.include_full_content is True

    def test_gen_run_from_row(self):
        row = {
            "id": "r1",
            "issue_id": "pi1",
            "job_name": "build-pdf",
            "trigger_source": "manual",
            "status": "completed",
            "error_text": "",
            "metrics_json": '{"pages":24}',
            "started_at": "2026-01-01",
            "finished_at": "2026-01-01",
            "created_at": "2026-01-01",
        }
        r = PublicationGenerationRun.from_row(row)
        assert r.job_name == "build-pdf"
        assert r.metrics_json == {"pages": 24}

    def test_delivery_from_row(self):
        row = {
            "id": "d1",
            "issue_id": "pi1",
            "email": "a@b.com",
            "channel": "email",
            "status": "sent",
            "provider": "sendgrid",
            "provider_message_id": "msg1",
            "error_text": "",
            "opened_at": "",
            "clicked_at": "",
            "sent_at": "2026-01-01",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        d = PublicationDelivery.from_row(row)
        assert d.channel == "email"
        assert d.provider == "sendgrid"

    def test_delivery_from_row_none(self):
        assert PublicationDelivery.from_row(None) is None


# ═══════════════════════════════════════════════════════════════
# Fake Newsletter Service
# ═══════════════════════════════════════════════════════════════
class FakeNewsletterService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Newsletter CRUD
    async def list_newsletters(self, org_id):
        self.calls.append(("list_newsletters", org_id))
        return [{"id": "n1"}]

    async def list_newsletters_by_owner(self, uid):
        self.calls.append(("list_newsletters_by_owner", uid))
        return [{"id": "n1"}]

    async def get_newsletter(self, nid):
        self.calls.append(("get_newsletter", nid))
        if nid == "missing":
            raise ValueError("Not found")
        return {"id": nid}

    async def create_newsletter(self, **kw):
        self.calls.append(("create_newsletter",))
        return {"id": "new-nl"}

    async def update_newsletter(self, nid, **kw):
        self.calls.append(("update_newsletter", nid))
        if nid == "missing":
            raise ValueError("Not found")
        return {"id": nid}

    async def delete_newsletter(self, nid):
        self.calls.append(("delete_newsletter", nid))
        if nid == "missing":
            raise ValueError("Not found")

    # Subscribers
    async def list_subscribers(self, nid, page=1, limit=20):
        self.calls.append(("list_subscribers", nid))
        return {"subscribers": [{"id": "s1"}], "page": page, "limit": limit}

    async def get_subscriber(self, sid):
        self.calls.append(("get_subscriber", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_subscriber(self, **kw):
        self.calls.append(("create_subscriber",))
        return {"id": "new-sub"}

    async def update_subscriber_status(self, sid, status):
        self.calls.append(("update_subscriber_status", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_subscriber(self, sid):
        self.calls.append(("delete_subscriber", sid))
        if sid == "missing":
            raise ValueError("Not found")

    # Issues
    async def list_issues(self, nid, page=1, limit=20):
        self.calls.append(("list_issues", nid))
        return {"issues": [{"id": "i1"}], "page": page, "limit": limit}

    async def get_issue(self, iid):
        self.calls.append(("get_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def create_issue(self, **kw):
        self.calls.append(("create_issue",))
        return {"id": "new-issue"}

    async def update_issue(self, iid, **kw):
        self.calls.append(("update_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def update_issue_status(self, iid, status):
        self.calls.append(("update_issue_status", iid, status))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def delete_issue(self, iid):
        self.calls.append(("delete_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")

    # Issue articles
    async def list_issue_articles(self, iid):
        self.calls.append(("list_issue_articles", iid))
        return [{"issue_id": iid, "article_id": "a1"}]

    async def add_issue_article(self, iid, article_id, sort_order, blurb):
        self.calls.append(("add_issue_article", iid))

    async def remove_issue_article(self, iid, article_id):
        self.calls.append(("remove_issue_article", iid, article_id))

    # Send events
    async def list_send_events(self, iid, page=1, limit=20):
        self.calls.append(("list_send_events", iid))
        return {"events": [{"id": "se1"}], "page": page, "limit": limit}

    async def create_send_event(self, **kw):
        self.calls.append(("create_send_event",))
        return {"id": "new-se"}

    # Segments
    async def list_segments(self, nid):
        self.calls.append(("list_segments", nid))
        return [{"id": "seg1"}]

    async def get_segment(self, sid):
        self.calls.append(("get_segment", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_segment(self, **kw):
        self.calls.append(("create_segment",))
        return {"id": "new-seg"}

    async def update_segment(self, sid, **kw):
        self.calls.append(("update_segment", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_segment(self, sid):
        self.calls.append(("delete_segment", sid))
        if sid == "missing":
            raise ValueError("Not found")


# ═══════════════════════════════════════════════════════════════
# Fake Publication Service
# ═══════════════════════════════════════════════════════════════
class FakePublicationService:
    def __init__(self, env, ctx=None):
        self.calls = []

    # Subscriptions
    async def list_subscriptions(self, page=1, limit=20):
        self.calls.append(("list_subscriptions",))
        return {"subscriptions": [{"id": "sub1"}], "page": page, "limit": limit}

    async def get_subscription(self, sid):
        self.calls.append(("get_subscription", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_subscription(self, **kw):
        self.calls.append(("create_subscription",))
        return {"id": "new-sub"}

    async def update_subscription_status(self, sid, status):
        self.calls.append(("update_subscription_status", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_subscription(self, sid):
        self.calls.append(("delete_subscription", sid))
        if sid == "missing":
            raise ValueError("Not found")

    # Issues
    async def list_issues(self, page=1, limit=20, issue_type=None):
        self.calls.append(("list_issues",))
        return {"issues": [{"id": "pi1"}], "page": page, "limit": limit}

    async def get_issue(self, iid):
        self.calls.append(("get_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def create_issue(self, **kw):
        self.calls.append(("create_issue",))
        return {"id": "new-pi"}

    async def update_issue(self, iid, **kw):
        self.calls.append(("update_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def approve_issue(self, iid, approved_by):
        self.calls.append(("approve_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def publish_issue(self, iid):
        self.calls.append(("publish_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def delete_issue(self, iid):
        self.calls.append(("delete_issue", iid))
        if iid == "missing":
            raise ValueError("Not found")

    # Items
    async def list_items(self, issue_id):
        self.calls.append(("list_items", issue_id))
        return [{"id": "it1"}]

    async def get_item(self, item_id):
        self.calls.append(("get_item", item_id))
        if item_id == "missing":
            raise ValueError("Not found")
        return {"id": item_id}

    async def create_item(self, **kw):
        self.calls.append(("create_item",))
        return {"id": "new-item"}

    async def update_item(self, item_id, **kw):
        self.calls.append(("update_item", item_id))
        if item_id == "missing":
            raise ValueError("Not found")
        return {"id": item_id}

    async def delete_item(self, item_id):
        self.calls.append(("delete_item", item_id))
        if item_id == "missing":
            raise ValueError("Not found")

    # Generation Runs
    async def list_gen_runs(self, issue_id):
        self.calls.append(("list_gen_runs", issue_id))
        return [{"id": "r1"}]

    async def create_gen_run(self, issue_id, job_name="", trigger_source="manual"):
        self.calls.append(("create_gen_run", issue_id))
        return {"id": "new-run"}

    async def update_gen_run(self, rid, status="", error_text="", metrics_json=None):
        self.calls.append(("update_gen_run", rid))
        if rid == "missing":
            raise ValueError("Not found")
        return {"id": rid}

    # Deliveries
    async def list_deliveries(self, issue_id, page=1, limit=20):
        self.calls.append(("list_deliveries", issue_id))
        return {"deliveries": [{"id": "d1"}], "page": page, "limit": limit}

    async def create_delivery(self, issue_id, email="", channel="email"):
        self.calls.append(("create_delivery", issue_id))
        return {"id": "new-del"}

    async def update_delivery_status(
        self, did, status="", provider="", provider_message_id="", error_text=""
    ):
        self.calls.append(("update_delivery_status", did))
        if did == "missing":
            raise ValueError("Not found")
        return {"id": did}


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


class NlClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig = nl_handler.NewsletterService
        nl_handler.NewsletterService = lambda env, ctx=None: self.svc
        try:
            return asyncio.run(
                nl_handler.handle_newsletters(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            nl_handler.NewsletterService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None, json_body=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json_body)


class PubClient:
    def __init__(self, svc_instance):
        self.svc = svc_instance

    def _dispatch(self, method, path, headers=None, json_body=None):
        parsed = urlparse(path)
        req = FakeRequest(
            method=method, url=path, headers=headers or {}, json_body=json_body
        )

        class _Env:
            JWT_SECRET = _JWT_SECRET

        orig = pub_handler.PublicationService
        pub_handler.PublicationService = lambda env, ctx=None: self.svc
        try:
            return asyncio.run(
                pub_handler.handle_publications(
                    req,
                    _Env(),
                    parsed.path,
                    method,
                    parse_qs(parsed.query),
                    FakeCtx(),
                )
            )
        finally:
            pub_handler.PublicationService = orig

    def get(self, path, headers=None):
        return self._dispatch("GET", path, headers=headers)

    def post(self, path, headers=None, json_body=None):
        return self._dispatch("POST", path, headers=headers, json_body=json_body)

    def put(self, path, headers=None, json_body=None):
        return self._dispatch("PUT", path, headers=headers, json_body=json_body)

    def delete(self, path, headers=None, json_body=None):
        return self._dispatch("DELETE", path, headers=headers, json_body=json_body)


@pytest.fixture
def nl_svc():
    return FakeNewsletterService(type("E", (), {})())


@pytest.fixture
def nl_client(nl_svc):
    return NlClient(nl_svc)


@pytest.fixture
def pub_svc():
    return FakePublicationService(type("E", (), {})())


@pytest.fixture
def pub_client(pub_svc):
    return PubClient(pub_svc)


# ═══════════════════════════════════════════════════════════════
# Newsletter Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestNewsletterHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, nl_client):
        resp = nl_client.get("/api/newsletters")
        assert resp.status_code == 401

    # Newsletter CRUD
    def test_list_newsletters(self, nl_client):
        resp = nl_client.get("/api/newsletters", headers=self._h())
        assert resp.status_code == 200
        assert "newsletters" in resp.json()

    def test_create_newsletter(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters",
            headers=self._h(),
            json_body={"name": "Test NL", "slug": "test-nl"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-nl"

    def test_get_newsletter(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1", headers=self._h())
        assert resp.status_code == 200

    def test_get_newsletter_missing(self, nl_client):
        resp = nl_client.get("/api/newsletters/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_newsletter(self, nl_client):
        resp = nl_client.put(
            "/api/newsletters/n1", headers=self._h(), json_body={"name": "Updated"}
        )
        assert resp.status_code == 200

    def test_delete_newsletter(self, nl_client):
        resp = nl_client.delete("/api/newsletters/n1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_newsletter_missing(self, nl_client):
        resp = nl_client.delete("/api/newsletters/missing", headers=self._h())
        assert resp.status_code == 404

    # Subscribers
    def test_list_subscribers(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/subscribers", headers=self._h())
        assert resp.status_code == 200
        assert "subscribers" in resp.json()

    def test_create_subscriber(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters/n1/subscribers",
            headers=self._h(),
            json_body={"email": "a@b.com"},
        )
        assert resp.status_code == 201

    def test_get_subscriber(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/subscribers/s1", headers=self._h())
        assert resp.status_code == 200

    def test_get_subscriber_missing(self, nl_client):
        resp = nl_client.get(
            "/api/newsletters/n1/subscribers/missing", headers=self._h()
        )
        assert resp.status_code == 404

    def test_update_subscriber(self, nl_client):
        resp = nl_client.put(
            "/api/newsletters/n1/subscribers/s1",
            headers=self._h(),
            json_body={"status": "confirmed"},
        )
        assert resp.status_code == 200

    def test_delete_subscriber(self, nl_client):
        resp = nl_client.delete("/api/newsletters/n1/subscribers/s1", headers=self._h())
        assert resp.status_code == 200

    # Issues
    def test_list_issues(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/issues", headers=self._h())
        assert resp.status_code == 200

    def test_create_issue(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters/n1/issues",
            headers=self._h(),
            json_body={"subject": "Test Issue"},
        )
        assert resp.status_code == 201

    def test_get_issue(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/issues/i1", headers=self._h())
        assert resp.status_code == 200

    def test_update_issue(self, nl_client):
        resp = nl_client.put(
            "/api/newsletters/n1/issues/i1",
            headers=self._h(),
            json_body={"subject": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_issue(self, nl_client):
        resp = nl_client.delete("/api/newsletters/n1/issues/i1", headers=self._h())
        assert resp.status_code == 200

    # Issue articles
    def test_list_issue_articles(self, nl_client):
        resp = nl_client.get(
            "/api/newsletters/n1/issues/i1/articles", headers=self._h()
        )
        assert resp.status_code == 200

    def test_add_issue_article(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters/n1/issues/i1/articles",
            headers=self._h(),
            json_body={"article_id": "a1"},
        )
        assert resp.status_code == 201

    def test_remove_issue_article(self, nl_client):
        resp = nl_client.delete(
            "/api/newsletters/n1/issues/i1/articles/a1", headers=self._h()
        )
        assert resp.status_code == 200

    # Send events
    def test_list_send_events(self, nl_client):
        resp = nl_client.get(
            "/api/newsletters/n1/issues/i1/send-events", headers=self._h()
        )
        assert resp.status_code == 200

    def test_create_send_event(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters/n1/issues/i1/send-events",
            headers=self._h(),
            json_body={"subscriber_id": "s1", "event_type": "open"},
        )
        assert resp.status_code == 201

    # Send action
    def test_send_issue(self, nl_client):
        resp = nl_client.post("/api/newsletters/n1/issues/i1/send", headers=self._h())
        assert resp.status_code == 200

    # Segments
    def test_list_segments(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/segments", headers=self._h())
        assert resp.status_code == 200

    def test_create_segment(self, nl_client):
        resp = nl_client.post(
            "/api/newsletters/n1/segments",
            headers=self._h(),
            json_body={"name": "Active"},
        )
        assert resp.status_code == 201

    def test_get_segment(self, nl_client):
        resp = nl_client.get("/api/newsletters/n1/segments/seg1", headers=self._h())
        assert resp.status_code == 200

    def test_update_segment(self, nl_client):
        resp = nl_client.put(
            "/api/newsletters/n1/segments/seg1",
            headers=self._h(),
            json_body={"name": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_segment(self, nl_client):
        resp = nl_client.delete("/api/newsletters/n1/segments/seg1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_segment_missing(self, nl_client):
        resp = nl_client.delete(
            "/api/newsletters/n1/segments/missing", headers=self._h()
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Publication Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestPublicationHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, pub_client):
        resp = pub_client.get("/api/publications/subscriptions")
        assert resp.status_code == 401

    # Subscriptions
    def test_list_subscriptions(self, pub_client):
        resp = pub_client.get("/api/publications/subscriptions", headers=self._h())
        assert resp.status_code == 200
        assert "subscriptions" in resp.json()

    def test_create_subscription(self, pub_client):
        resp = pub_client.post(
            "/api/publications/subscriptions",
            headers=self._h(),
            json_body={"email": "a@b.com"},
        )
        assert resp.status_code == 201

    def test_get_subscription(self, pub_client):
        resp = pub_client.get("/api/publications/subscriptions/sub1", headers=self._h())
        assert resp.status_code == 200

    def test_get_subscription_missing(self, pub_client):
        resp = pub_client.get(
            "/api/publications/subscriptions/missing", headers=self._h()
        )
        assert resp.status_code == 404

    def test_update_subscription(self, pub_client):
        resp = pub_client.put(
            "/api/publications/subscriptions/sub1",
            headers=self._h(),
            json_body={"status": "unsubscribed"},
        )
        assert resp.status_code == 200

    def test_delete_subscription(self, pub_client):
        resp = pub_client.delete(
            "/api/publications/subscriptions/sub1", headers=self._h()
        )
        assert resp.status_code == 200

    # Publication Issues
    def test_list_issues(self, pub_client):
        resp = pub_client.get("/api/publications/issues", headers=self._h())
        assert resp.status_code == 200

    def test_create_issue(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues",
            headers=self._h(),
            json_body={"title": "Jan Issue", "slug": "jan-issue"},
        )
        assert resp.status_code == 201

    def test_get_issue(self, pub_client):
        resp = pub_client.get("/api/publications/issues/pi1", headers=self._h())
        assert resp.status_code == 200

    def test_get_issue_missing(self, pub_client):
        resp = pub_client.get("/api/publications/issues/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_issue(self, pub_client):
        resp = pub_client.put(
            "/api/publications/issues/pi1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_issue(self, pub_client):
        resp = pub_client.delete("/api/publications/issues/pi1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_issue_missing(self, pub_client):
        resp = pub_client.delete("/api/publications/issues/missing", headers=self._h())
        assert resp.status_code == 404

    # Approve & Publish
    def test_approve_issue(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues/pi1/approve", headers=self._h()
        )
        assert resp.status_code == 200

    def test_publish_issue(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues/pi1/publish", headers=self._h()
        )
        assert resp.status_code == 200

    # Items
    def test_list_items(self, pub_client):
        resp = pub_client.get("/api/publications/issues/pi1/items", headers=self._h())
        assert resp.status_code == 200

    def test_create_item(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues/pi1/items",
            headers=self._h(),
            json_body={"article_id": "a1", "title": "Feature"},
        )
        assert resp.status_code == 201

    def test_get_item(self, pub_client):
        resp = pub_client.get(
            "/api/publications/issues/pi1/items/it1", headers=self._h()
        )
        assert resp.status_code == 200

    def test_update_item(self, pub_client):
        resp = pub_client.put(
            "/api/publications/issues/pi1/items/it1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_item(self, pub_client):
        resp = pub_client.delete(
            "/api/publications/issues/pi1/items/it1", headers=self._h()
        )
        assert resp.status_code == 200

    # Generation Runs
    def test_list_gen_runs(self, pub_client):
        resp = pub_client.get("/api/publications/issues/pi1/runs", headers=self._h())
        assert resp.status_code == 200

    def test_create_gen_run(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues/pi1/runs",
            headers=self._h(),
            json_body={"job_name": "build-pdf"},
        )
        assert resp.status_code == 201

    def test_update_gen_run(self, pub_client):
        resp = pub_client.put(
            "/api/publications/issues/pi1/runs/r1",
            headers=self._h(),
            json_body={"status": "completed"},
        )
        assert resp.status_code == 200

    # Deliveries
    def test_list_deliveries(self, pub_client):
        resp = pub_client.get(
            "/api/publications/issues/pi1/deliveries", headers=self._h()
        )
        assert resp.status_code == 200

    def test_create_delivery(self, pub_client):
        resp = pub_client.post(
            "/api/publications/issues/pi1/deliveries",
            headers=self._h(),
            json_body={"email": "a@b.com"},
        )
        assert resp.status_code == 201

    def test_update_delivery(self, pub_client):
        resp = pub_client.put(
            "/api/publications/issues/pi1/deliveries/d1",
            headers=self._h(),
            json_body={"status": "sent"},
        )
        assert resp.status_code == 200
