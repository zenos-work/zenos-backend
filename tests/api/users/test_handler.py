import importlib

import pytest


users_handler = importlib.import_module("api.users.handler")


class _Req:
    def __init__(self, method, path, body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._body = body
        self.body = body

    async def json(self):
        return self._body if self._body is not None else {}


class _UserObj:
    def __init__(self, user_id):
        self.id = user_id

    def to_dict(self, _scope=None):
        return {"id": self.id, "name": f"User {self.id}", "role": "AUTHOR"}


class _Svc:
    async def list_all(self, limit, offset):
        return (
            [
                {"id": "u-approver", "role": "APPROVER"},
                {"id": "u-super", "role": "SUPERADMIN"},
                {"id": "u-reader", "role": "READER"},
            ],
            3,
        )

    async def get_by_id(self, user_id, scope=None):
        if user_id == "missing":
            return None
        return _UserObj(user_id)

    async def get_prefs(self, user_id):
        if user_id == "few-topics":
            return {"topics": ["a"]}
        return {"topics": ["a", "b", "c"], "theme": "light"}

    async def list_reading_history(self, user_id, page, limit):
        return {"items": [{"article_id": "a1"}], "page": page, "limit": limit}

    async def upsert_reading_history_item(self, user_id, data):
        if data.get("article_id") == "bad":
            raise ValueError("invalid article")
        return {"article_id": data.get("article_id", "a1")}

    async def remove_reading_history_item(self, user_id, article_id):
        if article_id == "bad":
            raise ValueError("invalid article")

    async def clear_reading_history(self, user_id):
        return None

    async def update_profile(self, user_id, req, skip_name_update=False):
        return None

    async def update_prefs(self, user_id, topics, email_notifs, theme):
        return None

    async def self_upgrade_to_author(self, user_id):
        return None

    async def set_role(self, user_id, req):
        return None

    async def ban(self, user_id):
        return None

    async def unban(self, user_id):
        return None


class _AdminSvc:
    def __init__(self):
        self.notifications = []

    async def create_notification(self, **kwargs):
        self.notifications.append(kwargs)


class _DbRow:
    def __init__(self):
        self._bind_value = None

    def bind(self, value):
        self._bind_value = value
        return self

    async def run(self):
        return {"ok": True}

    async def first(self):
        return {"terms_accepted_at": "2026-03-26T10:00:00Z"}


class _Db:
    def prepare(self, sql):
        return _DbRow()


class _Env:
    def __init__(self):
        self.DB = _Db()


@pytest.fixture
def deps(monkeypatch):
    svc = _Svc()
    admin_svc = _AdminSvc()

    monkeypatch.setattr(users_handler, "UserService", lambda env, ctx: svc)
    monkeypatch.setattr(users_handler, "AdminService", lambda env, ctx: admin_svc)

    return svc, admin_svc


async def _dispatch(
    monkeypatch, method, path, *, body=None, user=None, role_ok=True, query=None
):
    async def _get_user(_request, _env):
        return user

    def _require_role(_user, allowed):
        return role_ok

    monkeypatch.setattr(users_handler, "get_user", _get_user)
    monkeypatch.setattr(users_handler, "require_role", _require_role)

    return await users_handler.handle_users(
        _Req(method, path, body=body),
        _Env(),
        path,
        method,
        query or {},
        object(),
    )


@pytest.mark.asyncio
async def test_approvers_get_auth_and_success(monkeypatch, deps):
    unauth = await _dispatch(monkeypatch, "GET", "/api/users/approvers", user=None)
    assert unauth.status_code == 401

    forbidden = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users/approvers",
        user={"sub": "u1", "role": "READER"},
        role_ok=False,
    )
    assert forbidden.status_code == 403

    ok = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users/approvers",
        user={"sub": "u1", "role": "AUTHOR"},
        role_ok=True,
    )
    assert ok.status_code == 200
    assert len(ok.json()["approvers"]) == 2


@pytest.mark.asyncio
async def test_approver_message_paths(monkeypatch, deps):
    _, admin_svc = deps

    missing_message = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/approvers/message",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"message": "   "},
    )
    assert missing_message.status_code == 422

    missing_recipients = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/approvers/message",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"message": "hello", "mode": "individual", "recipient_ids": []},
    )
    assert missing_recipients.status_code == 422

    no_valid_targets = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/approvers/message",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"message": "hello", "mode": "individual", "recipient_ids": ["u-reader"]},
    )
    assert no_valid_targets.status_code == 422

    ok = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/approvers/message",
        user={"sub": "u1", "role": "AUTHOR"},
        body={
            "message": "need review",
            "article_id": "a1",
            "mode": "individual",
            "recipient_ids": ["u-super"],
        },
    )
    assert ok.status_code == 200
    assert ok.json()["recipients"] == 1
    assert len(admin_svc.notifications) == 1


@pytest.mark.asyncio
async def test_user_me_and_list_endpoints(monkeypatch, deps):
    unauthorized = await _dispatch(monkeypatch, "GET", "/api/users", user=None)
    assert unauthorized.status_code == 401

    forbidden = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users",
        user={"sub": "u1", "role": "AUTHOR"},
        role_ok=False,
    )
    assert forbidden.status_code == 403

    listed = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users",
        user={"sub": "u1", "role": "APPROVER"},
        role_ok=True,
        query={"page": ["1"], "limit": ["200"]},
    )
    assert listed.status_code == 200
    assert listed.json()["pagination"]["limit"] == 100

    me_not_found = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users/me",
        user={"sub": "missing", "role": "AUTHOR"},
    )
    assert me_not_found.status_code == 404

    me_ok = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users/me",
        user={"sub": "few-topics", "role": "AUTHOR"},
    )
    assert me_ok.status_code == 200
    assert me_ok.json()["user"]["needs_topic_preferences"] is True


@pytest.mark.asyncio
async def test_user_profile_and_preferences_paths(monkeypatch, deps):
    bad_update = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/me",
        user={"sub": "u1", "role": "AUTHOR"},
        body={},
    )
    assert bad_update.status_code == 422

    prefs_ok = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/me/prefs",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"topics": ["x"], "email_notifs": 0, "theme": "light"},
    )
    assert prefs_ok.status_code == 200

    role_invalid = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/me/role",
        user={"sub": "u1", "role": "READER"},
        body={"role": "READER"},
    )
    assert role_invalid.status_code == 422


@pytest.mark.asyncio
async def test_reading_history_and_admin_role_paths(monkeypatch, deps):
    read_list = await _dispatch(
        monkeypatch,
        "GET",
        "/api/users/me/reading-history",
        user={"sub": "u1", "role": "AUTHOR"},
        query={"page": ["2"], "limit": ["3"]},
    )
    assert read_list.status_code == 200

    read_upsert_err = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/me/reading-history",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"article_id": "bad"},
    )
    assert read_upsert_err.status_code == 422

    read_remove_err = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/users/me/reading-history/bad",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert read_remove_err.status_code == 422

    clear_ok = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/users/me/reading-history",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert clear_ok.status_code == 200

    admin_forbidden = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/u2/role",
        user={"sub": "u1", "role": "APPROVER"},
        role_ok=False,
        body={"role": "AUTHOR"},
    )
    assert admin_forbidden.status_code == 403

    admin_bad_role = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/u2/role",
        user={"sub": "u1", "role": "SUPERADMIN"},
        role_ok=True,
        body={"role": "UNKNOWN"},
    )
    assert admin_bad_role.status_code == 422


@pytest.mark.asyncio
async def test_avatar_and_account_and_accept_terms_paths(monkeypatch, deps):
    class _MediaSvc:
        async def upload(self, user_id, request):
            if getattr(request, "_body", {}).get("mode") == "validation":
                raise ValueError("bad upload")
            if getattr(request, "_body", {}).get("mode") == "runtime":
                raise RuntimeError("storage down")
            return {"url": "https://cdn/avatar.jpg", "key": "avatars/u1.jpg"}

    monkeypatch.setattr(users_handler, "MediaService", lambda env, ctx: _MediaSvc())

    avatar_422 = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/me/avatar",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"mode": "validation"},
    )
    assert avatar_422.status_code == 422

    avatar_503 = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/me/avatar",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"mode": "runtime"},
    )
    assert avatar_503.status_code == 503

    avatar_ok = await _dispatch(
        monkeypatch,
        "POST",
        "/api/users/me/avatar",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"mode": "ok"},
    )
    assert avatar_ok.status_code == 201

    deactivate = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/users/me",
        user={"sub": "u1", "role": "AUTHOR"},
        body={"reason": "bye"},
    )
    assert deactivate.status_code == 200

    accepted = await _dispatch(
        monkeypatch,
        "PUT",
        "/api/users/me/accept-terms",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["terms_accepted"] is True

    not_found = await _dispatch(
        monkeypatch,
        "PATCH",
        "/api/users/me/unknown",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert not_found.status_code == 404
