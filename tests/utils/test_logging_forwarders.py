import base64
import importlib
import json
import sys

import pytest

from utils.log_models import LogEntry, LogLevel, LogType


@pytest.fixture
def module_with_fetch_loader():
    def _load(module_name, fetch_impl):
        js_mod = sys.modules["js"]
        js_mod.fetch = fetch_impl
        module = importlib.import_module(module_name)
        return importlib.reload(module)

    return _load


class TestLogModels:
    def test_log_entry_to_json_omits_none_and_formats_timestamp_ms(self):
        entry = LogEntry(
            level=LogLevel.INFO,
            type=LogType.EVENT,
            message="hello",
            trace_id="trace-123",
            timestamp=1700000000.123,
        )

        payload = json.loads(entry.to_json())

        assert payload["level"] == "INFO"
        assert payload["type"] == "event"
        assert payload["trace_id"] == "trace-123"
        assert payload["timestamp"] == 1700000000123
        assert "user_id" not in payload


class TestLokiForwarder:
    @pytest.mark.asyncio
    async def test_push_adds_basic_auth_and_payload(self, module_with_fetch_loader):
        calls = []

        async def fake_fetch(url, method=None, headers=None, body=None):
            calls.append(
                {"url": url, "method": method, "headers": headers, "body": body}
            )

        loki = module_with_fetch_loader("utils.loki", fake_fetch)

        entry = LogEntry(
            level=LogLevel.ERROR,
            type=LogType.ERROR,
            message="failure",
            service="zenos-api",
            env="staging",
            timestamp=1000.0,
        )

        forwarder = loki.LokiForwarder(
            "https://loki.example/", user="alice", password="secret"
        )
        await forwarder.push(entry)

        assert len(calls) == 1
        call = calls[0]
        assert call["url"] == "https://loki.example/loki/api/v1/push"
        assert call["method"] == "POST"
        assert call["headers"]["Content-Type"] == "application/json"
        expected_auth = base64.b64encode(b"alice:secret").decode()
        assert call["headers"]["Authorization"] == f"Basic {expected_auth}"

        payload = json.loads(call["body"])
        assert payload["streams"][0]["stream"]["service"] == "zenos-api"
        assert payload["streams"][0]["stream"]["env"] == "staging"

    @pytest.mark.asyncio
    async def test_push_swallows_fetch_exceptions(self, module_with_fetch_loader):
        async def failing_fetch(*_args, **_kwargs):
            raise RuntimeError("network down")

        loki = module_with_fetch_loader("utils.loki", failing_fetch)

        entry = LogEntry(level=LogLevel.INFO, type=LogType.EVENT, message="x")
        forwarder = loki.LokiForwarder("https://loki.example")

        await forwarder.push(entry)


class TestElkForwarder:
    @pytest.mark.asyncio
    async def test_push_builds_ndjson_with_api_key(self, module_with_fetch_loader):
        calls = []

        async def fake_fetch(url, method=None, headers=None, body=None):
            calls.append(
                {"url": url, "method": method, "headers": headers, "body": body}
            )

        elk = module_with_fetch_loader("utils.elk", fake_fetch)

        entry = LogEntry(level=LogLevel.WARN, type=LogType.EVENT, message="warn")
        forwarder = elk.ElkForwarder(
            "https://elk.example/", index="zenos-idx", api_key="abc123"
        )
        await forwarder.push(entry)

        assert len(calls) == 1
        call = calls[0]
        assert call["url"] == "https://elk.example/_bulk"
        assert call["method"] == "POST"
        assert call["headers"]["Content-Type"] == "application/x-ndjson"
        assert call["headers"]["Authorization"] == "ApiKey abc123"
        body_lines = call["body"].splitlines()
        assert len(body_lines) == 2
        assert json.loads(body_lines[0]) == {"index": {"_index": "zenos-idx"}}
        assert json.loads(body_lines[1])["message"] == "warn"


class TestForwarderFactory:
    def test_make_forwarder_priority_and_none_fallback(self, monkeypatch):
        forwarder_mod = importlib.import_module("utils.forwarder")

        class DummyElk:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        class DummyLoki:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        monkeypatch.setattr(forwarder_mod, "ElkForwarder", DummyElk)
        monkeypatch.setattr(forwarder_mod, "LokiForwarder", DummyLoki)

        class EnvElkAndLoki:
            ELK_URL = "https://elk"
            ELK_INDEX = "idx"
            ELK_API_KEY = "k"
            LOKI_URL = "https://loki"

        class EnvOnlyLoki:
            LOKI_URL = "https://loki"
            LOKI_USER = "u"
            LOKI_PASSWORD = "p"

        class EnvNone:
            pass

        selected = forwarder_mod.make_forwarder(EnvElkAndLoki())
        assert isinstance(selected, DummyElk)
        assert selected.kwargs["url"] == "https://elk"

        selected = forwarder_mod.make_forwarder(EnvOnlyLoki())
        assert isinstance(selected, DummyLoki)
        assert selected.kwargs["url"] == "https://loki"

        assert forwarder_mod.make_forwarder(EnvNone()) is None
