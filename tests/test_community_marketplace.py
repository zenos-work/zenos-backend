"""Tests for Phase 9 — Community, Marketplace, Referrals & Podcasts (model + handler)."""

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
comm_models = importlib.import_module("models.community.model")
CommunitySpace = comm_models.CommunitySpace
SpaceMember = comm_models.SpaceMember
CommunityPost = comm_models.CommunityPost

mkt_models = importlib.import_module("models.marketplace.model")
MarketplaceItem = mkt_models.MarketplaceItem
MarketplacePurchase = mkt_models.MarketplacePurchase
MarketplaceReview = mkt_models.MarketplaceReview

ref_models = importlib.import_module("models.referral.model")
ReferralCode = ref_models.ReferralCode
ReferralEvent = ref_models.ReferralEvent

pod_models = importlib.import_module("models.podcast.model")
PodcastShow = pod_models.PodcastShow
PodcastEpisode = pod_models.PodcastEpisode

comm_handler = importlib.import_module("api.community.handler")
mkt_handler = importlib.import_module("api.marketplace.handler")
ref_handler = importlib.import_module("api.referrals.handler")
pod_handler = importlib.import_module("api.podcasts.handler")
create_token = importlib.import_module("auth.jwt_handler").create_token

_JWT_SECRET = "test-secret"


# ═══════════════════════════════════════════════════════════════
# Community Model Tests
# ═══════════════════════════════════════════════════════════════
class TestCommunityModels:
    def test_space_from_row(self):
        row = {
            "id": "sp1",
            "org_id": "org1",
            "name": "General",
            "slug": "general",
            "description": "Main space",
            "cover_image_url": "",
            "icon": "💬",
            "space_type": "open",
            "membership_tier": "",
            "member_count": 42,
            "post_count": 10,
            "created_by": "u1",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        s = CommunitySpace.from_row(row)
        assert s.name == "General"
        assert s.member_count == 42
        assert s.icon == "💬"

    def test_space_from_row_none(self):
        assert CommunitySpace.from_row(None) is None

    def test_space_to_dict(self):
        s = CommunitySpace(id="sp1", name="Test", slug="test")
        d = s.to_dict()
        assert d["id"] == "sp1"
        assert d["name"] == "Test"
        assert d["member_count"] == 0

    def test_member_from_row(self):
        row = {
            "space_id": "sp1",
            "user_id": "u1",
            "role": "moderator",
            "joined_at": "2026-01-01",
        }
        m = SpaceMember.from_row(row)
        assert m.role == "moderator"
        assert m.space_id == "sp1"

    def test_member_from_row_none(self):
        assert SpaceMember.from_row(None) is None

    def test_member_to_dict(self):
        m = SpaceMember(space_id="sp1", user_id="u1")
        d = m.to_dict()
        assert d["space_id"] == "sp1"
        assert d["role"] == "member"

    def test_post_from_row(self):
        row = {
            "id": "p1",
            "space_id": "sp1",
            "author_id": "u1",
            "parent_id": "",
            "title": "Hello",
            "body": "World",
            "post_type": "discussion",
            "article_id": "",
            "status": "published",
            "pinned": 1,
            "reply_count": 3,
            "like_count": 5,
            "view_count": 100,
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        p = CommunityPost.from_row(row)
        assert p.title == "Hello"
        assert p.pinned is True
        assert p.reply_count == 3
        assert p.like_count == 5

    def test_post_from_row_none(self):
        assert CommunityPost.from_row(None) is None

    def test_post_to_dict(self):
        p = CommunityPost(id="p1", title="Test", body="Content")
        d = p.to_dict()
        assert d["id"] == "p1"
        assert d["pinned"] is False


# ═══════════════════════════════════════════════════════════════
# Marketplace Model Tests
# ═══════════════════════════════════════════════════════════════
class TestMarketplaceModels:
    def test_item_from_row(self):
        row = {
            "id": "it1",
            "seller_id": "u1",
            "org_id": "org1",
            "name": "Cool Widget",
            "slug": "cool-widget",
            "short_desc": "A widget",
            "long_desc": "A very cool widget",
            "item_type": "workflow",
            "category": "tools",
            "price_cents": 999,
            "currency": "USD",
            "pricing_model": "one_time",
            "preview_images": '["img1.png","img2.png"]',
            "asset_url": "",
            "workflow_id": "wf1",
            "status": "published",
            "is_featured": 1,
            "download_count": 50,
            "purchase_count": 10,
            "rating_avg": 4.5,
            "rating_count": 8,
            "published_at": "2026-01-01",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
        }
        i = MarketplaceItem.from_row(row)
        assert i.name == "Cool Widget"
        assert i.preview_images == ["img1.png", "img2.png"]
        assert i.price_cents == 999
        assert i.is_featured is True
        assert i.rating_avg == 4.5

    def test_item_from_row_none(self):
        assert MarketplaceItem.from_row(None) is None

    def test_item_to_dict(self):
        i = MarketplaceItem(id="it1", name="Test")
        d = i.to_dict()
        assert d["id"] == "it1"
        assert d["preview_images"] == []

    def test_item_default_preview_images(self):
        i = MarketplaceItem()
        assert i.preview_images == []

    def test_purchase_from_row(self):
        row = {
            "id": "pu1",
            "item_id": "it1",
            "buyer_id": "u2",
            "org_id": "",
            "payment_id": "pay1",
            "price_paid_cents": 999,
            "currency": "USD",
            "status": "completed",
            "purchased_at": "2026-01-01",
        }
        p = MarketplacePurchase.from_row(row)
        assert p.price_paid_cents == 999
        assert p.status == "completed"

    def test_purchase_from_row_none(self):
        assert MarketplacePurchase.from_row(None) is None

    def test_review_from_row(self):
        row = {
            "id": "rv1",
            "item_id": "it1",
            "reviewer_id": "u2",
            "rating": 5,
            "body": "Great!",
            "created_at": "2026-01-01",
        }
        r = MarketplaceReview.from_row(row)
        assert r.rating == 5
        assert r.body == "Great!"

    def test_review_from_row_none(self):
        assert MarketplaceReview.from_row(None) is None


# ═══════════════════════════════════════════════════════════════
# Referral Model Tests
# ═══════════════════════════════════════════════════════════════
class TestReferralModels:
    def test_code_from_row(self):
        row = {
            "id": "rc1",
            "user_id": "u1",
            "code": "ABC123",
            "total_clicks": 100,
            "total_signups": 20,
            "total_conversions": 5,
            "reward_credits": 50,
            "created_at": "2026-01-01",
        }
        c = ReferralCode.from_row(row)
        assert c.code == "ABC123"
        assert c.total_clicks == 100
        assert c.total_conversions == 5

    def test_code_from_row_none(self):
        assert ReferralCode.from_row(None) is None

    def test_code_to_dict(self):
        c = ReferralCode(id="rc1", code="ABC")
        d = c.to_dict()
        assert d["code"] == "ABC"
        assert d["total_clicks"] == 0

    def test_event_from_row(self):
        row = {
            "id": "ev1",
            "referral_code_id": "rc1",
            "event_type": "signup",
            "referred_user_id": "u2",
            "metadata": '{"source":"web"}',
            "created_at": "2026-01-01",
        }
        e = ReferralEvent.from_row(row)
        assert e.event_type == "signup"
        assert e.metadata == {"source": "web"}

    def test_event_from_row_none(self):
        assert ReferralEvent.from_row(None) is None

    def test_event_default_metadata(self):
        e = ReferralEvent()
        assert e.metadata == {}


# ═══════════════════════════════════════════════════════════════
# Podcast Model Tests
# ═══════════════════════════════════════════════════════════════
class TestPodcastModels:
    def test_show_from_row(self):
        row = {
            "id": "sh1",
            "owner_id": "u1",
            "org_id": "org1",
            "title": "Tech Talk",
            "slug": "tech-talk",
            "description": "A podcast",
            "cover_image_url": "",
            "rss_feed_url": "https://feed.xml",
            "created_at": "2026-01-01",
        }
        s = PodcastShow.from_row(row)
        assert s.title == "Tech Talk"
        assert s.rss_feed_url == "https://feed.xml"

    def test_show_from_row_none(self):
        assert PodcastShow.from_row(None) is None

    def test_show_to_dict(self):
        s = PodcastShow(id="sh1", title="Test")
        d = s.to_dict()
        assert d["id"] == "sh1"
        assert d["title"] == "Test"

    def test_episode_from_row(self):
        row = {
            "id": "ep1",
            "show_id": "sh1",
            "title": "Episode 1",
            "description": "First ep",
            "audio_url": "https://ep1.mp3",
            "duration_seconds": 3600,
            "episode_number": 1,
            "transcript_article_id": "art1",
            "published_at": "2026-01-01",
            "created_at": "2026-01-01",
        }
        e = PodcastEpisode.from_row(row)
        assert e.title == "Episode 1"
        assert e.duration_seconds == 3600
        assert e.episode_number == 1

    def test_episode_from_row_none(self):
        assert PodcastEpisode.from_row(None) is None

    def test_episode_to_dict(self):
        e = PodcastEpisode(id="ep1", title="Test", audio_url="test.mp3")
        d = e.to_dict()
        assert d["audio_url"] == "test.mp3"
        assert d["duration_seconds"] == 0


# ═══════════════════════════════════════════════════════════════
# Fake Community Service
# ═══════════════════════════════════════════════════════════════
class FakeCommunityService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_spaces(self, org_id, page=1, limit=20):
        self.calls.append(("list_spaces", org_id))
        return {"spaces": [{"id": "sp1"}], "page": page, "limit": limit}

    async def list_spaces_public(self, page=1, limit=20):
        self.calls.append(("list_spaces_public",))
        return {"spaces": [{"id": "sp1"}], "page": page, "limit": limit}

    async def get_space(self, sid):
        self.calls.append(("get_space", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_space(
        self,
        org_id,
        created_by,
        name,
        slug,
        description="",
        cover_image_url="",
        icon="",
        space_type="open",
        membership_tier="",
    ):
        self.calls.append(("create_space",))
        return {"id": "new-space"}

    async def update_space(self, sid, **kw):
        self.calls.append(("update_space", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_space(self, sid):
        self.calls.append(("delete_space", sid))
        if sid == "missing":
            raise ValueError("Not found")

    async def list_members(self, space_id, page=1, limit=20):
        self.calls.append(("list_members", space_id))
        return {"members": [{"user_id": "u1"}], "page": page, "limit": limit}

    async def join_space(self, space_id, user_id):
        self.calls.append(("join_space", space_id, user_id))
        return {"joined": True}

    async def leave_space(self, space_id, user_id):
        self.calls.append(("leave_space", space_id, user_id))
        return {"left": True}

    async def update_member_role(self, space_id, user_id, role):
        self.calls.append(("update_member_role", space_id, user_id))
        if user_id == "missing":
            raise ValueError("Not found")
        return {"updated": True}

    async def list_posts(self, space_id, page=1, limit=20):
        self.calls.append(("list_posts", space_id))
        return {"posts": [{"id": "p1"}], "page": page, "limit": limit}

    async def list_replies(self, parent_id, page=1, limit=20):
        self.calls.append(("list_replies", parent_id))
        return {"replies": [{"id": "r1"}], "page": page, "limit": limit}

    async def get_post(self, pid):
        self.calls.append(("get_post", pid))
        if pid == "missing":
            raise ValueError("Not found")
        return {"id": pid}

    async def create_post(
        self,
        space_id,
        author_id,
        title="",
        body="",
        post_type="discussion",
        article_id="",
        parent_id="",
    ):
        self.calls.append(("create_post",))
        return {"id": "new-post"}

    async def update_post(self, pid, **kw):
        self.calls.append(("update_post", pid))
        if pid == "missing":
            raise ValueError("Not found")
        return {"id": pid}

    async def delete_post(self, pid):
        self.calls.append(("delete_post", pid))
        if pid == "missing":
            raise ValueError("Not found")

    async def like_post(self, pid):
        self.calls.append(("like_post", pid))
        if pid == "missing":
            raise ValueError("Not found")
        return {"liked": True}


# ═══════════════════════════════════════════════════════════════
# Fake Marketplace Service
# ═══════════════════════════════════════════════════════════════
class FakeMarketplaceService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_items(self, page=1, limit=20, category=None, seller_id=None):
        self.calls.append(("list_items",))
        return {"items": [{"id": "it1"}], "page": page, "limit": limit}

    async def get_item(self, iid):
        self.calls.append(("get_item", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def create_item(
        self,
        seller_id,
        name,
        slug,
        short_desc,
        category,
        org_id="",
        long_desc="",
        item_type="",
        price_cents=0,
        currency="USD",
        pricing_model="one_time",
        preview_images=None,
        asset_url="",
        workflow_id="",
    ):
        self.calls.append(("create_item",))
        return {"id": "new-item"}

    async def update_item(self, iid, **kw):
        self.calls.append(("update_item", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid}

    async def delete_item(self, iid):
        self.calls.append(("delete_item", iid))
        if iid == "missing":
            raise ValueError("Not found")

    async def publish_item(self, iid):
        self.calls.append(("publish_item", iid))
        if iid == "missing":
            raise ValueError("Not found")
        return {"id": iid, "status": "published"}

    async def list_purchases(self, buyer_id, page=1, limit=20):
        self.calls.append(("list_purchases", buyer_id))
        return {"purchases": [{"id": "pu1"}], "page": page, "limit": limit}

    async def list_item_purchases(self, item_id, page=1, limit=20):
        self.calls.append(("list_item_purchases", item_id))
        return {"purchases": [{"id": "pu1"}], "page": page, "limit": limit}

    async def purchase_item(
        self,
        item_id,
        buyer_id,
        org_id="",
        payment_id="",
        price_paid_cents=0,
        currency="USD",
    ):
        self.calls.append(("purchase_item", item_id))
        return {"id": "new-purchase"}

    async def list_reviews(self, item_id, page=1, limit=20):
        self.calls.append(("list_reviews", item_id))
        return {"reviews": [{"id": "rv1"}], "page": page, "limit": limit}

    async def create_review(self, item_id, reviewer_id, rating, body=""):
        self.calls.append(("create_review", item_id))
        return {"id": "new-review"}

    async def delete_review(self, rid):
        self.calls.append(("delete_review", rid))
        if rid == "missing":
            raise ValueError("Not found")


# ═══════════════════════════════════════════════════════════════
# Fake Referral Service
# ═══════════════════════════════════════════════════════════════
class FakeReferralService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def get_or_create_code(self, user_id):
        self.calls.append(("get_or_create_code", user_id))
        return {"id": "rc1", "code": "ABC123"}

    async def get_stats(self, user_id):
        self.calls.append(("get_stats", user_id))
        if user_id == "missing":
            raise ValueError("Not found")
        return {"id": "rc1", "code": "ABC123", "total_clicks": 10}

    async def track_event(self, code, event_type, referred_user_id="", metadata=None):
        self.calls.append(("track_event", code, event_type))
        if code == "INVALID":
            raise ValueError("Invalid referral code")
        return {"id": "new-event"}

    async def list_events(self, user_id, page=1, limit=20):
        self.calls.append(("list_events", user_id))
        if user_id == "missing":
            raise ValueError("Not found")
        return {"events": [{"id": "ev1"}], "page": page, "limit": limit}


# ═══════════════════════════════════════════════════════════════
# Fake Podcast Service
# ═══════════════════════════════════════════════════════════════
class FakePodcastService:
    def __init__(self, env, ctx=None):
        self.calls = []

    async def list_shows(self, page=1, limit=20):
        self.calls.append(("list_shows",))
        return {"shows": [{"id": "sh1"}], "page": page, "limit": limit}

    async def list_shows_by_owner(self, owner_id):
        self.calls.append(("list_shows_by_owner", owner_id))
        return [{"id": "sh1"}]

    async def get_show(self, sid):
        self.calls.append(("get_show", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def create_show(
        self,
        owner_id,
        title,
        slug,
        org_id="",
        description="",
        cover_image_url="",
        rss_feed_url="",
    ):
        self.calls.append(("create_show",))
        return {"id": "new-show"}

    async def update_show(self, sid, **kw):
        self.calls.append(("update_show", sid))
        if sid == "missing":
            raise ValueError("Not found")
        return {"id": sid}

    async def delete_show(self, sid):
        self.calls.append(("delete_show", sid))
        if sid == "missing":
            raise ValueError("Not found")

    async def list_episodes(self, show_id, page=1, limit=20):
        self.calls.append(("list_episodes", show_id))
        return {"episodes": [{"id": "ep1"}], "page": page, "limit": limit}

    async def get_episode(self, eid):
        self.calls.append(("get_episode", eid))
        if eid == "missing":
            raise ValueError("Not found")
        return {"id": eid}

    async def create_episode(
        self,
        show_id,
        title,
        audio_url,
        description="",
        duration_seconds=0,
        episode_number=0,
        transcript_article_id="",
        published_at="",
    ):
        self.calls.append(("create_episode",))
        return {"id": "new-ep"}

    async def update_episode(self, eid, **kw):
        self.calls.append(("update_episode", eid))
        if eid == "missing":
            raise ValueError("Not found")
        return {"id": eid}

    async def delete_episode(self, eid):
        self.calls.append(("delete_episode", eid))
        if eid == "missing":
            raise ValueError("Not found")


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
def comm_svc():
    return FakeCommunityService(type("E", (), {})())


@pytest.fixture
def comm_client(comm_svc):
    return _make_client(comm_handler, "handle_community", "CommunityService", comm_svc)


@pytest.fixture
def mkt_svc():
    return FakeMarketplaceService(type("E", (), {})())


@pytest.fixture
def mkt_client(mkt_svc):
    return _make_client(
        mkt_handler, "handle_marketplace", "MarketplaceService", mkt_svc
    )


@pytest.fixture
def ref_svc():
    return FakeReferralService(type("E", (), {})())


@pytest.fixture
def ref_client(ref_svc):
    return _make_client(ref_handler, "handle_referrals", "ReferralService", ref_svc)


@pytest.fixture
def pod_svc():
    return FakePodcastService(type("E", (), {})())


@pytest.fixture
def pod_client(pod_svc):
    return _make_client(pod_handler, "handle_podcasts", "PodcastService", pod_svc)


# ═══════════════════════════════════════════════════════════════
# Community Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestCommunityHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, comm_client):
        resp = comm_client.get("/api/community")
        assert resp.status_code == 401

    # Spaces CRUD
    def test_list_spaces_public(self, comm_client):
        resp = comm_client.get("/api/community", headers=self._h())
        assert resp.status_code == 200
        assert "spaces" in resp.json()

    def test_list_spaces_by_org(self, comm_client):
        resp = comm_client.get("/api/community?org_id=org1", headers=self._h())
        assert resp.status_code == 200

    def test_create_space(self, comm_client):
        resp = comm_client.post(
            "/api/community",
            headers=self._h(),
            json_body={"name": "Test", "slug": "test"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-space"

    def test_get_space(self, comm_client):
        resp = comm_client.get("/api/community/sp1", headers=self._h())
        assert resp.status_code == 200

    def test_get_space_missing(self, comm_client):
        resp = comm_client.get("/api/community/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_space(self, comm_client):
        resp = comm_client.put(
            "/api/community/sp1", headers=self._h(), json_body={"name": "Updated"}
        )
        assert resp.status_code == 200

    def test_delete_space(self, comm_client):
        resp = comm_client.delete("/api/community/sp1", headers=self._h())
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_space_missing(self, comm_client):
        resp = comm_client.delete("/api/community/missing", headers=self._h())
        assert resp.status_code == 404

    # Members
    def test_list_members(self, comm_client):
        resp = comm_client.get("/api/community/sp1/members", headers=self._h())
        assert resp.status_code == 200
        assert "members" in resp.json()

    def test_join_space(self, comm_client):
        resp = comm_client.post("/api/community/sp1/members", headers=self._h())
        assert resp.status_code == 201

    def test_leave_space(self, comm_client):
        resp = comm_client.delete("/api/community/sp1/members", headers=self._h())
        assert resp.status_code == 200

    def test_update_member_role(self, comm_client):
        resp = comm_client.put(
            "/api/community/sp1/members/u2",
            headers=self._h(),
            json_body={"role": "moderator"},
        )
        assert resp.status_code == 200

    def test_update_member_role_missing(self, comm_client):
        resp = comm_client.put(
            "/api/community/sp1/members/missing",
            headers=self._h(),
            json_body={"role": "moderator"},
        )
        assert resp.status_code == 404

    # Posts
    def test_list_posts(self, comm_client):
        resp = comm_client.get("/api/community/sp1/posts", headers=self._h())
        assert resp.status_code == 200
        assert "posts" in resp.json()

    def test_create_post(self, comm_client):
        resp = comm_client.post(
            "/api/community/sp1/posts",
            headers=self._h(),
            json_body={"title": "Hello", "body": "World"},
        )
        assert resp.status_code == 201

    def test_get_post(self, comm_client):
        resp = comm_client.get("/api/community/sp1/posts/p1", headers=self._h())
        assert resp.status_code == 200

    def test_get_post_missing(self, comm_client):
        resp = comm_client.get("/api/community/sp1/posts/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_post(self, comm_client):
        resp = comm_client.put(
            "/api/community/sp1/posts/p1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_post(self, comm_client):
        resp = comm_client.delete("/api/community/sp1/posts/p1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_post_missing(self, comm_client):
        resp = comm_client.delete("/api/community/sp1/posts/missing", headers=self._h())
        assert resp.status_code == 404

    # Replies
    def test_list_replies(self, comm_client):
        resp = comm_client.get("/api/community/sp1/posts/p1/replies", headers=self._h())
        assert resp.status_code == 200
        assert "replies" in resp.json()

    # Like
    def test_like_post(self, comm_client):
        resp = comm_client.post("/api/community/sp1/posts/p1/like", headers=self._h())
        assert resp.status_code == 200

    def test_like_post_missing(self, comm_client):
        resp = comm_client.post(
            "/api/community/sp1/posts/missing/like", headers=self._h()
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Marketplace Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestMarketplaceHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, mkt_client):
        resp = mkt_client.get("/api/marketplace")
        assert resp.status_code == 401

    # Items CRUD
    def test_list_items(self, mkt_client):
        resp = mkt_client.get("/api/marketplace", headers=self._h())
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_create_item(self, mkt_client):
        resp = mkt_client.post(
            "/api/marketplace",
            headers=self._h(),
            json_body={
                "name": "Widget",
                "slug": "widget",
                "short_desc": "A widget",
                "category": "tools",
            },
        )
        assert resp.status_code == 201

    def test_get_item(self, mkt_client):
        resp = mkt_client.get("/api/marketplace/it1", headers=self._h())
        assert resp.status_code == 200

    def test_get_item_missing(self, mkt_client):
        resp = mkt_client.get("/api/marketplace/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_item(self, mkt_client):
        resp = mkt_client.put(
            "/api/marketplace/it1", headers=self._h(), json_body={"name": "Updated"}
        )
        assert resp.status_code == 200

    def test_delete_item(self, mkt_client):
        resp = mkt_client.delete("/api/marketplace/it1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_item_missing(self, mkt_client):
        resp = mkt_client.delete("/api/marketplace/missing", headers=self._h())
        assert resp.status_code == 404

    # Publish
    def test_publish_item(self, mkt_client):
        resp = mkt_client.post("/api/marketplace/it1/publish", headers=self._h())
        assert resp.status_code == 200

    def test_publish_item_missing(self, mkt_client):
        resp = mkt_client.post("/api/marketplace/missing/publish", headers=self._h())
        assert resp.status_code == 404

    # Purchases
    def test_list_item_purchases(self, mkt_client):
        resp = mkt_client.get("/api/marketplace/it1/purchases", headers=self._h())
        assert resp.status_code == 200

    def test_purchase_item(self, mkt_client):
        resp = mkt_client.post(
            "/api/marketplace/it1/purchases",
            headers=self._h(),
            json_body={"price_paid_cents": 999},
        )
        assert resp.status_code == 201

    def test_my_purchases(self, mkt_client):
        resp = mkt_client.get("/api/marketplace/my-purchases", headers=self._h())
        assert resp.status_code == 200

    # Reviews
    def test_list_reviews(self, mkt_client):
        resp = mkt_client.get("/api/marketplace/it1/reviews", headers=self._h())
        assert resp.status_code == 200

    def test_create_review(self, mkt_client):
        resp = mkt_client.post(
            "/api/marketplace/it1/reviews",
            headers=self._h(),
            json_body={"rating": 5, "body": "Great!"},
        )
        assert resp.status_code == 201

    def test_delete_review(self, mkt_client):
        resp = mkt_client.delete("/api/marketplace/it1/reviews/rv1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_review_missing(self, mkt_client):
        resp = mkt_client.delete(
            "/api/marketplace/it1/reviews/missing", headers=self._h()
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════
# Referral Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestReferralHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, ref_client):
        resp = ref_client.get("/api/referrals")
        assert resp.status_code == 401

    def test_generate_code(self, ref_client):
        resp = ref_client.post("/api/referrals", headers=self._h())
        assert resp.status_code == 201
        assert resp.json()["code"] == "ABC123"

    def test_get_stats(self, ref_client):
        resp = ref_client.get("/api/referrals", headers=self._h())
        assert resp.status_code == 200

    def test_get_stats_route(self, ref_client):
        resp = ref_client.get("/api/referrals/stats", headers=self._h())
        assert resp.status_code == 200

    def test_track_event(self, ref_client):
        resp = ref_client.post(
            "/api/referrals/track",
            headers=self._h(),
            json_body={"code": "ABC123", "event_type": "click"},
        )
        assert resp.status_code == 201

    def test_track_event_invalid_code(self, ref_client):
        resp = ref_client.post(
            "/api/referrals/track",
            headers=self._h(),
            json_body={"code": "INVALID", "event_type": "click"},
        )
        assert resp.status_code == 400

    def test_list_events(self, ref_client):
        resp = ref_client.get("/api/referrals/events", headers=self._h())
        assert resp.status_code == 200
        assert "events" in resp.json()


# ═══════════════════════════════════════════════════════════════
# Podcast Handler Tests
# ═══════════════════════════════════════════════════════════════
class TestPodcastHandler:
    def _h(self):
        return {"Authorization": f"Bearer {_token()}"}

    def test_unauth_returns_401(self, pod_client):
        resp = pod_client.get("/api/podcasts")
        assert resp.status_code == 401

    # Shows CRUD
    def test_list_shows(self, pod_client):
        resp = pod_client.get("/api/podcasts", headers=self._h())
        assert resp.status_code == 200
        assert "shows" in resp.json()

    def test_list_shows_by_owner(self, pod_client):
        resp = pod_client.get("/api/podcasts?owner_id=u1", headers=self._h())
        assert resp.status_code == 200

    def test_create_show(self, pod_client):
        resp = pod_client.post(
            "/api/podcasts",
            headers=self._h(),
            json_body={"title": "Tech Talk", "slug": "tech-talk"},
        )
        assert resp.status_code == 201

    def test_get_show(self, pod_client):
        resp = pod_client.get("/api/podcasts/sh1", headers=self._h())
        assert resp.status_code == 200

    def test_get_show_missing(self, pod_client):
        resp = pod_client.get("/api/podcasts/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_show(self, pod_client):
        resp = pod_client.put(
            "/api/podcasts/sh1", headers=self._h(), json_body={"title": "Updated"}
        )
        assert resp.status_code == 200

    def test_delete_show(self, pod_client):
        resp = pod_client.delete("/api/podcasts/sh1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_show_missing(self, pod_client):
        resp = pod_client.delete("/api/podcasts/missing", headers=self._h())
        assert resp.status_code == 404

    # Episodes
    def test_list_episodes(self, pod_client):
        resp = pod_client.get("/api/podcasts/sh1/episodes", headers=self._h())
        assert resp.status_code == 200
        assert "episodes" in resp.json()

    def test_create_episode(self, pod_client):
        resp = pod_client.post(
            "/api/podcasts/sh1/episodes",
            headers=self._h(),
            json_body={"title": "Ep 1", "audio_url": "ep1.mp3"},
        )
        assert resp.status_code == 201

    def test_get_episode(self, pod_client):
        resp = pod_client.get("/api/podcasts/sh1/episodes/ep1", headers=self._h())
        assert resp.status_code == 200

    def test_get_episode_missing(self, pod_client):
        resp = pod_client.get("/api/podcasts/sh1/episodes/missing", headers=self._h())
        assert resp.status_code == 404

    def test_update_episode(self, pod_client):
        resp = pod_client.put(
            "/api/podcasts/sh1/episodes/ep1",
            headers=self._h(),
            json_body={"title": "Updated"},
        )
        assert resp.status_code == 200

    def test_delete_episode(self, pod_client):
        resp = pod_client.delete("/api/podcasts/sh1/episodes/ep1", headers=self._h())
        assert resp.status_code == 200

    def test_delete_episode_missing(self, pod_client):
        resp = pod_client.delete(
            "/api/podcasts/sh1/episodes/missing", headers=self._h()
        )
        assert resp.status_code == 404
