import importlib

import pytest


membership_handler = importlib.import_module("api.membership.handler")


class _Req:
    def __init__(self, method, path, body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._body = body or {}

    async def json(self):
        return self._body


class _Ctx:
    class log:
        @staticmethod
        async def error(_msg):
            return None


class _Env:
    pass


class _Svc:
    async def get_membership_plans(self):
        return [{"id": "free"}]

    async def get_user_membership(self, user_id):
        if user_id == "missing":
            return None
        if user_id == "boom":
            raise RuntimeError("db")
        return {"tier": "creator_pro", "is_active": True}

    async def upgrade_membership(self, user_id, new_tier, stripe_subscription_id):
        if user_id == "boom":
            raise RuntimeError("write")
        return {
            "user_id": user_id,
            "tier": new_tier,
            "stripe_subscription_id": stripe_subscription_id,
        }

    async def track_premium_read(
        self, user_id, article_id, scroll_depth, duration_seconds
    ):
        if article_id == "boom":
            raise RuntimeError("fail")
        return {
            "user_id": user_id,
            "article_id": article_id,
            "scroll_depth": scroll_depth,
            "duration_seconds": duration_seconds,
        }

    async def log_premium_funnel_event(self, **kwargs):
        if kwargs.get("event_type") == "boom":
            raise RuntimeError("fail")
        return kwargs


@pytest.fixture
def svc(monkeypatch):
    s = _Svc()
    monkeypatch.setattr(membership_handler, "MembershipService", lambda env, ctx: s)
    return s


class TestMembershipHandler:
    @pytest.mark.asyncio
    async def test_plans_success_and_error(self, monkeypatch, svc):
        ok = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/plans"),
            _Env(),
            "/api/membership/plans",
            "GET",
            {},
            _Ctx(),
        )
        assert ok.status_code == 200

        class _BadSvc(_Svc):
            async def get_membership_plans(self):
                raise RuntimeError("x")

        monkeypatch.setattr(
            membership_handler, "MembershipService", lambda env, ctx: _BadSvc()
        )
        bad = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/plans"),
            _Env(),
            "/api/membership/plans",
            "GET",
            {},
            _Ctx(),
        )
        assert bad.status_code == 500

    @pytest.mark.asyncio
    async def test_me_paths(self, monkeypatch, svc):
        async def _no_user(_r, _e):
            return None

        monkeypatch.setattr(membership_handler, "get_user", _no_user)
        unauth = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/me"),
            _Env(),
            "/api/membership/me",
            "GET",
            {},
            _Ctx(),
        )
        assert unauth.status_code == 401

        async def _missing(_r, _e):
            return {"sub": "missing"}

        monkeypatch.setattr(membership_handler, "get_user", _missing)
        not_found = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/me"),
            _Env(),
            "/api/membership/me",
            "GET",
            {},
            _Ctx(),
        )
        assert not_found.status_code == 404

        async def _ok(_r, _e):
            return {"sub": "u1"}

        monkeypatch.setattr(membership_handler, "get_user", _ok)
        ok = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/me"),
            _Env(),
            "/api/membership/me",
            "GET",
            {},
            _Ctx(),
        )
        assert ok.status_code == 200

        async def _boom(_r, _e):
            return {"sub": "boom"}

        monkeypatch.setattr(membership_handler, "get_user", _boom)
        bad = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/me"),
            _Env(),
            "/api/membership/me",
            "GET",
            {},
            _Ctx(),
        )
        assert bad.status_code == 500

    @pytest.mark.asyncio
    async def test_upgrade_paths(self, monkeypatch, svc):
        async def _no_user(_r, _e):
            return None

        monkeypatch.setattr(membership_handler, "get_user", _no_user)
        unauth = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/upgrade", {"tier": "creator_pro"}),
            _Env(),
            "/api/membership/upgrade",
            "POST",
            {},
            _Ctx(),
        )
        assert unauth.status_code == 401

        async def _ok(_r, _e):
            return {"sub": "u1"}

        monkeypatch.setattr(membership_handler, "get_user", _ok)
        bad_tier = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/upgrade", {"tier": "gold"}),
            _Env(),
            "/api/membership/upgrade",
            "POST",
            {},
            _Ctx(),
        )
        assert bad_tier.status_code == 400

        ok = await membership_handler.handle_membership(
            _Req(
                "POST",
                "/api/membership/upgrade",
                {"tier": "team_suite", "stripe_subscription_id": "sub_1"},
            ),
            _Env(),
            "/api/membership/upgrade",
            "POST",
            {},
            _Ctx(),
        )
        assert ok.status_code == 201

        async def _boom(_r, _e):
            return {"sub": "boom"}

        monkeypatch.setattr(membership_handler, "get_user", _boom)
        err = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/upgrade", {"tier": "free"}),
            _Env(),
            "/api/membership/upgrade",
            "POST",
            {},
            _Ctx(),
        )
        assert err.status_code == 500

    @pytest.mark.asyncio
    async def test_premium_read_paths(self, monkeypatch, svc):
        async def _no_user(_r, _e):
            return None

        monkeypatch.setattr(membership_handler, "get_user", _no_user)
        unauth = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/premium-read", {"article_id": "a1"}),
            _Env(),
            "/api/membership/premium-read",
            "POST",
            {},
            _Ctx(),
        )
        assert unauth.status_code == 401

        async def _ok(_r, _e):
            return {"sub": "u1"}

        monkeypatch.setattr(membership_handler, "get_user", _ok)
        missing = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/premium-read", {}),
            _Env(),
            "/api/membership/premium-read",
            "POST",
            {},
            _Ctx(),
        )
        assert missing.status_code == 400

        ok = await membership_handler.handle_membership(
            _Req(
                "POST",
                "/api/membership/premium-read",
                {"article_id": "a1", "scroll_depth": 0.75, "duration_seconds": 12},
            ),
            _Env(),
            "/api/membership/premium-read",
            "POST",
            {},
            _Ctx(),
        )
        assert ok.status_code == 201

        boom = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/premium-read", {"article_id": "boom"}),
            _Env(),
            "/api/membership/premium-read",
            "POST",
            {},
            _Ctx(),
        )
        assert boom.status_code == 500

    @pytest.mark.asyncio
    async def test_funnel_and_not_found(self, monkeypatch, svc):
        async def _anon(_r, _e):
            return None

        monkeypatch.setattr(membership_handler, "get_user", _anon)
        missing = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/funnel-event", {}),
            _Env(),
            "/api/membership/funnel-event",
            "POST",
            {},
            _Ctx(),
        )
        assert missing.status_code == 400

        ok = await membership_handler.handle_membership(
            _Req(
                "POST", "/api/membership/funnel-event", {"event_type": "viewed_paywall"}
            ),
            _Env(),
            "/api/membership/funnel-event",
            "POST",
            {},
            _Ctx(),
        )
        assert ok.status_code == 201

        async def _auth(_r, _e):
            return {"sub": "u2"}

        monkeypatch.setattr(membership_handler, "get_user", _auth)
        ok_auth = await membership_handler.handle_membership(
            _Req(
                "POST",
                "/api/membership/funnel-event",
                {"event_type": "clicked_upgrade"},
            ),
            _Env(),
            "/api/membership/funnel-event",
            "POST",
            {},
            _Ctx(),
        )
        assert ok_auth.status_code == 201

        err = await membership_handler.handle_membership(
            _Req("POST", "/api/membership/funnel-event", {"event_type": "boom"}),
            _Env(),
            "/api/membership/funnel-event",
            "POST",
            {},
            _Ctx(),
        )
        assert err.status_code == 500

        not_found = await membership_handler.handle_membership(
            _Req("GET", "/api/membership/unknown"),
            _Env(),
            "/api/membership/unknown",
            "GET",
            {},
            _Ctx(),
        )
        assert not_found.status_code == 404
