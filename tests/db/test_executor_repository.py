import pytest
import db.executor as executor_module

from db.executor import D1Executor
from db.repository import BaseRepository


class _Prepared:
    def __init__(self, state):
        self._state = state
        self._params = ()

    def bind(self, *params):
        self._params = params
        self._state["bound"].append(params)
        return self

    async def run(self):
        if self._state.get("raise") == "run":
            raise RuntimeError("run failed")
        self._state["run_calls"] += 1

    async def first(self):
        if self._state.get("raise") == "first":
            raise RuntimeError("first failed")
        return self._state.get("first_result")

    async def all(self):
        if self._state.get("raise") == "all":
            raise RuntimeError("all failed")

        class _Res:
            def __init__(self, results):
                self.results = results

        results = self._state.get("all_result")
        return _Res(results) if results is not None else None


class _DB:
    def __init__(self, state):
        self._state = state

    def prepare(self, sql):
        self._state["queries"].append(sql)
        return _Prepared(self._state)


class _Ctx:
    class _Log:
        def __init__(self):
            self.calls = []

        def debug(self, name, event_data=None):
            self.calls.append(("debug", name, event_data))

        def error(self, msg, event_data=None):
            self.calls.append(("error", msg, event_data))

    def __init__(self):
        self.log = self._Log()


class _AsyncCtx:
    class _Log:
        def __init__(self):
            self.calls = []

        async def debug(self, name, event_data=None):
            self.calls.append((name, event_data))

    def __init__(self):
        self.log = self._Log()


class _Model:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_row(cls, row):
        return cls(row["value"])


class TestD1Executor:
    @pytest.mark.asyncio
    async def test_run_first_all_success(self):
        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": {"id": 1},
            "all_result": [{"id": 1}, {"id": 2}],
        }
        ex = D1Executor(_DB(state), _Ctx())

        await ex.run("UPDATE x SET y=?", 1)
        first = await ex.first("SELECT * FROM x WHERE id=?", 1)
        all_rows = await ex.all("SELECT * FROM x")

        assert state["run_calls"] == 1
        assert first == {"id": 1}
        assert all_rows == [{"id": 1}, {"id": 2}]

    @pytest.mark.asyncio
    async def test_first_and_all_empty_results(self):
        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
        }
        ex = D1Executor(_DB(state), _Ctx())

        first = await ex.first("SELECT 1")
        all_rows = await ex.all("SELECT 1")

        assert first is None
        assert all_rows == []

    @pytest.mark.asyncio
    async def test_executor_normalizes_undefined_like_object_to_none(self):
        class UndefinedLike:
            def __str__(self) -> str:
                return "undefined"

        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
        }
        ex = D1Executor(_DB(state), _Ctx())

        await ex.run("UPDATE x SET a=?", UndefinedLike())

        assert state["bound"][-1] == (None,)

    @pytest.mark.asyncio
    async def test_executor_prefers_js_null_for_null_like_values(self, monkeypatch):
        class UndefinedLike:
            def __str__(self) -> str:
                return "undefined"

        sentinel_null = object()
        monkeypatch.setattr(executor_module, "js_null", sentinel_null)

        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
        }
        ex = D1Executor(_DB(state), _Ctx())

        await ex.run("UPDATE x SET a=?, b=?", UndefinedLike(), "null")

        assert state["bound"][-1] == (None, None)

    @pytest.mark.asyncio
    async def test_executor_normalizes_object_undefined_shape(self):
        class UndefinedObjectLike:
            def __str__(self) -> str:
                return "[object Undefined]"

        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
        }
        ex = D1Executor(_DB(state), _Ctx())

        await ex.run("UPDATE x SET a=?", UndefinedObjectLike())

        assert state["bound"][-1] == (None,)

    @pytest.mark.asyncio
    async def test_executor_awaits_async_debug_logger(self):
        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
        }
        ctx = _AsyncCtx()
        ex = D1Executor(_DB(state), ctx)

        await ex.run("UPDATE x SET a=?", 1)

        assert len(ctx.log.calls) == 1

    @pytest.mark.asyncio
    async def test_exceptions_are_reraised(self):
        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": None,
            "all_result": None,
            "raise": "run",
        }
        ex = D1Executor(_DB(state), _Ctx())

        with pytest.raises(RuntimeError, match="run failed"):
            await ex.run("UPDATE x", 1)

        state["raise"] = "first"
        with pytest.raises(RuntimeError, match="first failed"):
            await ex.first("SELECT x")

        state["raise"] = "all"
        with pytest.raises(RuntimeError, match="all failed"):
            await ex.all("SELECT x")


class TestBaseRepository:
    @pytest.mark.asyncio
    async def test_find_and_execute_proxy_to_executor(self):
        state = {
            "queries": [],
            "bound": [],
            "run_calls": 0,
            "first_result": {"id": 10},
            "all_result": [{"id": 10}],
        }
        repo = BaseRepository(_DB(state), _Ctx())

        one = await repo.find_one("SELECT one", 1)
        many = await repo.find_all("SELECT many")
        await repo.execute("DELETE x", 1)

        assert one == {"id": 10}
        assert many == [{"id": 10}]
        assert state["run_calls"] == 1

    def test_map_helpers(self):
        repo = BaseRepository(_DB({"queries": [], "bound": [], "run_calls": 0}), None)

        assert repo.map_one(None, _Model) is None

        mapped_one = repo.map_one({"value": "a"}, _Model)
        mapped_many = repo.map_many([{"value": "a"}, {"value": "b"}], _Model)

        assert mapped_one.value == "a"
        assert [x.value for x in mapped_many] == ["a", "b"]
