import importlib

import pytest


media_handler = importlib.import_module("api.media.handler")


class _Req:
    def __init__(self, method, path, body=None):
        self.method = method
        self.url = f"https://test.local{path}"
        self.headers = {}
        self._body = body

    async def json(self):
        return self._body if self._body is not None else {}


class _Obj:
    def __init__(self):
        self.body = b"hello"
        self.httpMetadata = {"contentType": "text/plain"}


class _Svc:
    async def get_public(self, key):
        if key == "boom":
            raise RuntimeError("storage down")
        if key == "missing":
            return None
        return _Obj()

    async def upload(self, user_id, request):
        mode = (await request.json()).get("mode")
        if mode == "value":
            raise ValueError("invalid file")
        if mode == "runtime":
            raise RuntimeError("storage down")
        return {"key": "uploads/u1/a.png", "url": "https://cdn/a.png"}

    async def delete(self, user_id, key, is_superadmin=False):
        if key == "deny":
            raise PermissionError("forbidden")
        if key == "boom":
            raise RuntimeError("storage down")


class _Env:
    pass


@pytest.fixture
def patch_service(monkeypatch):
    svc = _Svc()
    monkeypatch.setattr(media_handler, "MediaService", lambda env, ctx: svc)
    return svc


async def _dispatch(monkeypatch, method, path, *, user=None, role_ok=False, body=None):
    async def _get_user(_request, _env):
        return user

    monkeypatch.setattr(media_handler, "get_user", _get_user)
    monkeypatch.setattr(media_handler, "require_role", lambda u, roles: role_ok)

    return await media_handler.handle_media(
        _Req(method, path, body=body),
        _Env(),
        path,
        method,
        {},
        object(),
    )


@pytest.mark.asyncio
async def test_public_get_paths(monkeypatch, patch_service):
    ok = await _dispatch(monkeypatch, "GET", "/api/media/path/to/file.jpg")
    assert ok.status_code == 200

    missing = await _dispatch(monkeypatch, "GET", "/api/media/missing")
    assert missing.status_code == 404

    err = await _dispatch(monkeypatch, "GET", "/api/media/boom")
    assert err.status_code == 503


@pytest.mark.asyncio
async def test_upload_paths(monkeypatch, patch_service):
    unauth = await _dispatch(monkeypatch, "POST", "/api/media/upload", user=None)
    assert unauth.status_code == 401

    bad = await _dispatch(
        monkeypatch,
        "POST",
        "/api/media/upload",
        user={"sub": "u1"},
        body={"mode": "value"},
    )
    assert bad.status_code == 422

    down = await _dispatch(
        monkeypatch,
        "POST",
        "/api/media/upload",
        user={"sub": "u1"},
        body={"mode": "runtime"},
    )
    assert down.status_code == 503

    ok = await _dispatch(
        monkeypatch,
        "POST",
        "/api/media/upload",
        user={"sub": "u1"},
        body={"mode": "ok"},
    )
    assert ok.status_code == 201


@pytest.mark.asyncio
async def test_delete_and_not_found_paths(monkeypatch, patch_service):
    denied = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/media/deny",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert denied.status_code == 403

    down = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/media/boom",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert down.status_code == 503

    ok = await _dispatch(
        monkeypatch,
        "DELETE",
        "/api/media/any-key",
        user={"sub": "u1", "role": "SUPERADMIN"},
        role_ok=True,
    )
    assert ok.status_code == 200

    not_found = await _dispatch(
        monkeypatch,
        "PATCH",
        "/api/media/any-key",
        user={"sub": "u1", "role": "AUTHOR"},
    )
    assert not_found.status_code == 404
