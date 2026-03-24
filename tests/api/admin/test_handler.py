import importlib

import pytest


admin_handler = importlib.import_module("api.admin.handler")


class _Req:
    def __init__(self, method, path):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}


class _ReqJson(_Req):
    """Request stub with a JSON body (for POST tests)."""

    def __init__(self, method, path, body):
        super().__init__(method, path)
        self._body = body

    async def json(self):
        return self._body


class _Env:
    DB = None


class _Ctx:
    trace_id = "trace-1"


class _Svc:
    def __init__(self):
        self.calls = []

    async def get_stats(self):
        self.calls.append("get_stats")
        return {"ok": "stats"}

    async def get_approval_queue(self, page):
        self.calls.append(("get_approval_queue", page))
        return {"queue": [], "pagination": {"page": page}}

    async def list_users(self, page):
        self.calls.append(("list_users", page))
        return {"users": [], "pagination": {"page": page}}

    async def ban_user(self, user_id):
        self.calls.append(("ban_user", user_id))

    async def unban_user(self, user_id):
        self.calls.append(("unban_user", user_id))

    async def get_notifications(self, user_id, page):
        self.calls.append(("get_notifications", user_id, page))
        return {"notifications": [], "pagination": {"page": page}}

    async def mark_notifications_read(self, user_id):
        self.calls.append(("mark_notifications_read", user_id))

    async def list_content_types(self):
        self.calls.append("list_content_types")
        return {"content_types": [{"slug": "article", "name": "Article"}]}

    async def create_content_type(self, payload, actor_id):
        self.calls.append(("create_content_type", payload))
        return {"content_type": {"slug": "deep-dive", "name": payload.get("name", "")}}


@pytest.fixture
def svc(monkeypatch):
    s = _Svc()
    monkeypatch.setattr(admin_handler, "AdminService", lambda env, ctx: s)
    return s


@pytest.fixture
def allow_all(monkeypatch):
    monkeypatch.setattr(admin_handler, "require_role", lambda user, allowed: True)


class TestAdminHandler:
    @pytest.mark.asyncio
    async def test_requires_authentication(self, monkeypatch, svc):
        async def _no_user(_request, _env):
            return None

        monkeypatch.setattr(admin_handler, "get_user", _no_user)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/stats"),
            _Env(),
            "/api/admin/stats",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_stats_forbidden_without_role(self, monkeypatch, svc):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "AUTHOR"}

        monkeypatch.setattr(admin_handler, "get_user", _user)
        monkeypatch.setattr(admin_handler, "require_role", lambda user, allowed: False)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/stats"),
            _Env(),
            "/api/admin/stats",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_stats_success(self, monkeypatch, svc, allow_all):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/stats"),
            _Env(),
            "/api/admin/stats",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 200
        assert resp.json()["ok"] == "stats"
        assert "get_stats" in svc.calls

    @pytest.mark.asyncio
    async def test_queue_and_users_routes(self, monkeypatch, svc, allow_all):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "APPROVER"}

        monkeypatch.setattr(admin_handler, "get_user", _user)

        queue_resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/queue?page=2"),
            _Env(),
            "/api/admin/queue",
            "GET",
            {"page": ["2"]},
            _Ctx(),
        )
        users_resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/users?page=3"),
            _Env(),
            "/api/admin/users",
            "GET",
            {"page": ["3"]},
            _Ctx(),
        )

        assert queue_resp.status_code == 200
        assert users_resp.status_code == 200
        assert ("get_approval_queue", 2) in svc.calls
        assert ("list_users", 3) in svc.calls

    @pytest.mark.asyncio
    async def test_user_ban_unban_and_notifications(self, monkeypatch, svc, allow_all):
        async def _user(_request, _env):
            return {"sub": "u-notify", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)

        ban = await admin_handler.handle_admin(
            _Req("PUT", "/api/admin/users/u2/ban"),
            _Env(),
            "/api/admin/users/u2/ban",
            "PUT",
            {},
            _Ctx(),
        )
        unban = await admin_handler.handle_admin(
            _Req("PUT", "/api/admin/users/u2/unban"),
            _Env(),
            "/api/admin/users/u2/unban",
            "PUT",
            {},
            _Ctx(),
        )
        notif = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/notifications?page=4"),
            _Env(),
            "/api/admin/notifications",
            "GET",
            {"page": ["4"]},
            _Ctx(),
        )
        read = await admin_handler.handle_admin(
            _Req("PUT", "/api/admin/notifications/read"),
            _Env(),
            "/api/admin/notifications/read",
            "PUT",
            {},
            _Ctx(),
        )

        assert ban.status_code == 200
        assert unban.status_code == 200
        assert notif.status_code == 200
        assert read.status_code == 200
        assert ("ban_user", "u2") in svc.calls
        assert ("unban_user", "u2") in svc.calls
        assert ("get_notifications", "u-notify", 4) in svc.calls
        assert ("mark_notifications_read", "u-notify") in svc.calls

    @pytest.mark.asyncio
    async def test_unknown_route_returns_not_found(self, monkeypatch, svc):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)
        monkeypatch.setattr(admin_handler, "require_role", lambda user, allowed: True)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/does-not-exist"),
            _Env(),
            "/api/admin/does-not-exist",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_content_types_get_forbidden_without_superadmin(
        self, monkeypatch, svc
    ):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "AUTHOR"}

        monkeypatch.setattr(admin_handler, "get_user", _user)
        monkeypatch.setattr(admin_handler, "require_role", lambda user, allowed: False)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/content-types"),
            _Env(),
            "/api/admin/content-types",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_content_types_get_success(self, monkeypatch, svc, allow_all):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)

        resp = await admin_handler.handle_admin(
            _Req("GET", "/api/admin/content-types"),
            _Env(),
            "/api/admin/content-types",
            "GET",
            {},
            _Ctx(),
        )

        assert resp.status_code == 200
        assert "list_content_types" in svc.calls

    @pytest.mark.asyncio
    async def test_content_types_post_success(self, monkeypatch, svc, allow_all):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)

        req = _ReqJson("POST", "/api/admin/content-types", {"name": "Deep Dive"})
        resp = await admin_handler.handle_admin(
            req,
            _Env(),
            "/api/admin/content-types",
            "POST",
            {},
            _Ctx(),
        )

        assert resp.status_code == 201
        assert any("create_content_type" in str(c) for c in svc.calls)

    @pytest.mark.asyncio
    async def test_content_types_post_validation_error(self, monkeypatch):
        async def _user(_request, _env):
            return {"sub": "u1", "role": "SUPERADMIN"}

        monkeypatch.setattr(admin_handler, "get_user", _user)
        monkeypatch.setattr(admin_handler, "require_role", lambda u, a: True)

        class _SvcRaisesValue:
            async def create_content_type(self, payload, actor_id):
                raise ValueError("name must be at least 2 characters")

        monkeypatch.setattr(
            admin_handler, "AdminService", lambda env, ctx: _SvcRaisesValue()
        )

        req = _ReqJson("POST", "/api/admin/content-types", {"name": "x"})
        resp = await admin_handler.handle_admin(
            req,
            _Env(),
            "/api/admin/content-types",
            "POST",
            {},
            _Ctx(),
        )

        assert resp.status_code == 422
