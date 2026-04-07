import importlib
import sys
import types

import pytest


js_stub = sys.modules.get("js")
if js_stub is None:
    js_stub = types.ModuleType("js")
    sys.modules["js"] = js_stub


async def _unused_fetch(*_args, **_kwargs):
    raise RuntimeError("fetch not configured in test")


if not hasattr(js_stub, "fetch"):
    js_stub.fetch = _unused_fetch
if not hasattr(js_stub, "Headers"):
    js_stub.Headers = types.SimpleNamespace(new=lambda v: dict(v))


google = importlib.import_module("auth.google")


class _Resp:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload


class _Env:
    GOOGLE_CLIENT_ID = "cid"
    GOOGLE_CLIENT_SECRET = "sec"
    FRONTEND_URL = "https://app.example.com"


def _obj(**kwargs):
    return types.SimpleNamespace(**kwargs)


@pytest.mark.asyncio
async def test_exchange_code_token_error(monkeypatch):
    calls = []

    async def _fetch(url, **kwargs):
        calls.append((url, kwargs))
        return _Resp(400, _obj(error="invalid_grant"))

    monkeypatch.setattr(google, "js_fetch", _fetch)
    monkeypatch.setattr(google, "Headers", types.SimpleNamespace(new=lambda v: dict(v)))

    result = await google.exchange_code("bad-code", _Env())
    assert result["error"] == "Google token exchange failed"
    assert calls[0][0] == google.GOOGLE_TOKEN_URL


@pytest.mark.asyncio
async def test_exchange_code_userinfo_error(monkeypatch):
    responses = [
        _Resp(200, _obj(access_token="token-123")),
        _Resp(200, _obj(name="No ID")),
    ]

    async def _fetch(url, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(google, "js_fetch", _fetch)
    monkeypatch.setattr(google, "Headers", types.SimpleNamespace(new=lambda v: dict(v)))

    result = await google.exchange_code("ok-code", _Env())
    assert result["error"] == "Google auth failed"


@pytest.mark.asyncio
async def test_exchange_code_success(monkeypatch):
    responses = [
        _Resp(200, _obj(access_token="token-123")),
        _Resp(200, _obj(id="g1", email="user@example.com", name="User", picture="pic")),
    ]

    async def _fetch(url, **kwargs):
        return responses.pop(0)

    monkeypatch.setattr(google, "js_fetch", _fetch)
    monkeypatch.setattr(google, "Headers", types.SimpleNamespace(new=lambda v: dict(v)))

    result = await google.exchange_code("ok-code", _Env())
    assert result["id"] == "g1"
    assert result["email"] == "user@example.com"
    assert result["picture"] == "pic"
