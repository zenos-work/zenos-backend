import importlib
import json
import sys
import types

import pytest

from utils.helpers import (
    _json_default,
    _frontend_origin,
    calc_read_time,
    cors_headers,
    error,
    paginate,
    resolve_allowed_origin,
    slugify,
    unique_slug,
)


class TestHelpers:
    def test_json_default_handles_to_py_and_raises_for_unknown(self):
        class WithToPyNoArg:
            def to_py(self):
                return {"k": "v"}

        class WithToPyDepthFallback:
            def to_py(self, depth=None):
                if depth is None:
                    raise TypeError("needs depth")
                return {"depth": depth}

        assert _json_default(WithToPyNoArg()) == {"k": "v"}
        assert _json_default(WithToPyDepthFallback()) == {"depth": 5}

        with pytest.raises(TypeError):
            _json_default(object())

    def test_frontend_origin_and_allowed_origin(self, simple_request_factory):
        class EnvWithUrl:
            FRONTEND_URL = "https://frontend.example.com/some/path"

        class EnvWithoutUrl:
            pass

        req_same = simple_request_factory(
            headers={"Origin": "https://frontend.example.com"}
        )
        req_other = simple_request_factory(
            headers={"Origin": "https://evil.example.com"}
        )

        assert _frontend_origin(EnvWithUrl()) == "https://frontend.example.com"
        assert _frontend_origin(EnvWithoutUrl()) == "*"
        assert resolve_allowed_origin(EnvWithoutUrl(), req_same) == "*"
        assert (
            resolve_allowed_origin(EnvWithUrl(), None) == "https://frontend.example.com"
        )
        assert (
            resolve_allowed_origin(EnvWithUrl(), req_same)
            == "https://frontend.example.com"
        )
        assert (
            resolve_allowed_origin(EnvWithUrl(), req_other)
            == "https://frontend.example.com"
        )

    def test_cors_error_and_utilities(
        self, monkeypatch, development_env, simple_request_factory
    ):
        req = simple_request_factory(headers={"Origin": "https://app.zenos.dev"})

        headers = cors_headers(
            env=development_env,
            request=req,
            content_type=None,
            allow_credentials=True,
            extra_headers=[("X-Test", "1")],
        )

        assert "Content-Type" not in headers
        assert headers["Access-Control-Allow-Origin"] == "https://app.zenos.dev"
        assert headers["Access-Control-Allow-Credentials"] == "true"
        assert headers["X-Test"] == "1"

        err_resp = error(
            "missing",
            status=404,
            details={"hint": "x"},
            env=development_env,
            request=req,
        )
        payload = err_resp.json()
        assert err_resp.status_code == 404
        assert payload["error"]["code"] == "NOT_FOUND"
        assert payload["error"]["hint"] == "x"

        assert slugify(" Hello, World!   Foo__Bar ") == "hello-world-foo-bar"

        monkeypatch.setattr("utils.helpers.new_id", lambda: "12345678-abcd")
        assert unique_slug("Test Title") == "test-title-12345678"

        assert calc_read_time("one two three", wpm=200) == 1
        assert calc_read_time(" ".join(["w"] * 450), wpm=200) == 3
        assert paginate(0, 500) == (100, 0)
        assert paginate(2, 10) == (10, 10)


class TestLogger:
    @pytest.mark.asyncio
    async def test_logger_emits_debug_only_in_development(
        self, monkeypatch, development_env
    ):
        logger_mod = importlib.import_module("utils.logger")

        class FakeForwarder:
            def __init__(self):
                self.entries = []

            async def push(self, entry):
                self.entries.append(entry)

        fwd = FakeForwarder()
        monkeypatch.setattr(logger_mod, "make_forwarder", lambda _env: fwd)

        printed = []
        monkeypatch.setattr("builtins.print", lambda msg: printed.append(msg))

        log = logger_mod.Logger(
            development_env, trace_id="t1", user_id="u1", user_role="AUTHOR"
        )

        await log.debug("dbg")
        await log.info("info", event_name="evt")
        await log.warn("warn")
        await log.request("GET", "/x")
        await log.response("GET", "/x", 500, 12.345)
        await log.event("evt", {"a": 1})
        await log.analytics("ana", {"b": 2})

        assert len(fwd.entries) == 7
        assert all(entry.trace_id == "t1" for entry in fwd.entries)
        assert any(entry.level == "DEBUG" for entry in fwd.entries)
        assert any(
            entry.type == "response" and entry.status == 500 for entry in fwd.entries
        )
        assert printed

        class ProdEnv:
            ENVIRONMENT = "production"

        prod_log = logger_mod.Logger(ProdEnv())
        await prod_log.debug("nope")
        assert len(fwd.entries) == 7

    @pytest.mark.asyncio
    async def test_logger_error_populates_exception_fields(
        self, monkeypatch, development_env
    ):
        logger_mod = importlib.import_module("utils.logger")

        class FakeForwarder:
            def __init__(self):
                self.entries = []

            async def push(self, entry):
                self.entries.append(entry)

        fwd = FakeForwarder()
        monkeypatch.setattr(logger_mod, "make_forwarder", lambda _env: fwd)
        monkeypatch.setattr("builtins.print", lambda *_args, **_kwargs: None)

        log = logger_mod.Logger(development_env)

        try:
            raise ValueError("bad value")
        except ValueError as exc:
            await log.error("failed", exc=exc)

        entry = fwd.entries[-1]
        assert entry.level == "ERROR"
        assert entry.error_type == "ValueError"
        assert entry.error_msg == "bad value"
        assert entry.error_traceback is not None
        assert entry.error_line is not None


class TestIndexRouting:
    @pytest.mark.asyncio
    async def test_dispatch_routes_and_default_not_found(
        self, development_env, simple_request_factory
    ):
        # Pre-stub imported router modules so index routing can be tested in isolation.
        route_calls = []

        def _install_route_module(module_name, func_name, tag, auth_style=False):
            mod = types.ModuleType(module_name)
            if auth_style:

                async def _handler(request, env, path):
                    route_calls.append((tag, path, request.method))
                    return sys.modules["js"].Response.new(
                        json.dumps({"ok": tag}), status=200, headers={}
                    )

            else:

                async def _handler(request, env, path, method, query, ctx):
                    route_calls.append((tag, path, method, query))
                    return sys.modules["js"].Response.new(
                        json.dumps({"ok": tag}), status=200, headers={}
                    )

            setattr(mod, func_name, _handler)
            sys.modules[module_name] = mod

        _install_route_module("auth.router", "handle_auth", "auth", auth_style=True)
        _install_route_module("api.articles.handler", "handle_articles", "articles")
        _install_route_module("api.users.handler", "handle_users", "users")
        _install_route_module("api.tags.handler", "handle_tags", "tags")
        _install_route_module("api.comments.handler", "handle_comments", "comments")
        _install_route_module("api.social.handler", "handle_social", "social")
        _install_route_module("api.feed.handler", "handle_feed", "feed")
        _install_route_module("api.media.handler", "handle_media", "media")
        _install_route_module("api.admin.handler", "handle_admin", "admin")
        _install_route_module("api.search.handler", "handle_search", "search")

        if "workers" not in sys.modules:
            workers_stub = types.ModuleType("workers")

            class WorkerEntrypoint:
                pass

            workers_stub.WorkerEntrypoint = WorkerEntrypoint
            sys.modules["workers"] = workers_stub

        sys.modules.pop("index", None)
        index = importlib.import_module("index")
        index = importlib.reload(index)

        app = index.Default()
        app.env = development_env

        class Ctx:
            def __init__(self, req):
                self.request = req
                self.env = development_env
                self.trace_id = "trace-1"

        options_resp = await app._dispatch(
            Ctx(simple_request_factory(method="OPTIONS", url="https://test.local/x"))
        )
        assert options_resp.status_code == 204

        health_resp = await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/health"))
        )
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "ok"

        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/auth/google"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/articles?q=1"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/users"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/tags"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/comments"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/social"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/feed"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/media"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/admin"))
        )
        await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/api/search"))
        )

        not_found = await app._dispatch(
            Ctx(simple_request_factory(url="https://test.local/nope"))
        )
        assert not_found.status_code == 404

        routed_names = [item[0] for item in route_calls]
        assert "auth" in routed_names
        for expected in [
            "articles",
            "users",
            "tags",
            "comments",
            "social",
            "feed",
            "media",
            "admin",
            "search",
        ]:
            assert expected in routed_names
