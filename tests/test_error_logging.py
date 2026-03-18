import sys
import types

import pytest

if "js" in sys.modules and not hasattr(sys.modules["js"], "fetch"):
    sys.modules["js"].fetch = None

if "pyodide.ffi" not in sys.modules:
    ffi_stub = types.ModuleType("pyodide.ffi")
    ffi_stub.to_js = lambda value: value
    pyodide_stub = types.ModuleType("pyodide")
    pyodide_stub.ffi = ffi_stub
    sys.modules["pyodide"] = pyodide_stub
    sys.modules["pyodide.ffi"] = ffi_stub

from api.media.repository import MediaRepository
from api.media.service import MediaService
from middleware.logging import with_logging


class EnvWithoutMedia:
    ENVIRONMENT = "development"


class FakeRequest:
    method = "POST"
    url = "https://testserver/api/media/upload"
    headers = {}


@pytest.mark.asyncio
async def test_media_service_allows_missing_media_binding_until_use():
    svc = MediaService(EnvWithoutMedia())

    assert svc._repo._r2 is None


@pytest.mark.asyncio
async def test_repository_converts_python_bytes_before_r2_put(monkeypatch):
    converted = object()

    class FakeBucket:
        def __init__(self):
            self.calls = []

        async def put(self, key, body, httpMetadata=None):
            self.calls.append((key, body, httpMetadata))

    bucket = FakeBucket()
    repo = MediaRepository(bucket)

    monkeypatch.setattr("api.media.repository.to_js", lambda body: converted)

    key = await repo.upload("user-1", "image/png", b"abc", 3)

    assert key.startswith("uploads/user-1/")
    assert bucket.calls[0][1] is converted
    assert bucket.calls[0][2] == {"contentType": "image/png"}


@pytest.mark.asyncio
async def test_with_logging_returns_development_debug_payload():
    async def failing_handler(ctx):
        raise RuntimeError("boom")

    response = await with_logging(FakeRequest(), EnvWithoutMedia(), failing_handler)

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "INTERNAL_ERROR"
    assert payload["error"]["trace_id"]
    assert payload["error"]["debug"]["type"] == "RuntimeError"
    assert payload["error"]["debug"]["message"] == "boom"
    assert payload["error"]["debug"]["line"] is not None
    assert payload["error"]["debug"]["stack_trace"]
