import inspect
from typing import Optional, Any

try:
    # pyodide.ffi.to_js(None) creates a JsProxy wrapping JS null.
    # Unlike js_JSON.parse("null") (which auto-converts JS null → Python None),
    # to_js(None) produces a non-None Python proxy that, when passed as an
    # argument to a JS function, correctly delivers JS null (not undefined).
    from pyodide.ffi import to_js as _pyodide_to_js

    js_null = _pyodide_to_js(None)
except ImportError:  # pragma: no cover - local test environment
    js_null = None


class D1Executor:
    """
    Thin wrapper around the Cloudflare D1 binding.
    Centralises prepare/bind/run/first/all so repositories
    never call env.DB directly — only through this class.
    Benefits:
    - Single place to add query logging / timing
    - Easy to swap in a mock for unit tests
    - Consistent error handling for all DB calls
    """

    def __init__(self, db, ctx=None):
        self._db = db
        self._ctx = ctx

    def _null_value(self):
        # D1 reliably binds Python None to SQL NULL in this runtime.
        # Returning JS proxy null here can surface as unsupported undefined.
        return None

    @staticmethod
    def _is_null_like_string(value: str) -> bool:
        lowered = value.strip().lower()
        return lowered in {
            "undefined",
            "null",
            "[object undefined]",
            "[object null]",
        }

    def _normalize_param(self, value: Any) -> Any:
        if value is None:
            return self._null_value()

        # Fast-path for JS undefined/null objects exposed by Python Workers.
        # These may not be Python strings, but their string representation is
        # often "undefined"/"null" and D1 bind rejects them.
        try:
            rendered = str(value).strip().lower()
            if self._is_null_like_string(rendered):
                return self._null_value()
        except Exception:
            pass

        # In Python Workers, optional fields may arrive as JS `undefined` proxies.
        to_py = getattr(value, "to_py", None)
        if callable(to_py):
            try:
                value = to_py()
            except TypeError:
                value = to_py(depth=5)

        if value is None:
            return self._null_value()

        if isinstance(value, str):
            if self._is_null_like_string(value):
                return self._null_value()

        try:
            rendered = str(value).strip().lower()
            if self._is_null_like_string(rendered):
                return self._null_value()
        except Exception:
            pass

        primitive_types = (str, int, float, bool, bytes, bytearray, memoryview)
        if isinstance(value, primitive_types):
            return value

        # Last-resort guard: prevent JS proxy-like objects from reaching D1 bind.
        try:
            rendered = str(value).strip().lower()
            if self._is_null_like_string(rendered):
                return self._null_value()
            return str(value)
        except Exception:
            return self._null_value()

    def _normalize_params(self, params: tuple) -> tuple:
        return tuple(self._normalize_param(p) for p in params)

    async def run(self, sql: str, *params) -> None:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            await self._db.prepare(sql).bind(*normalized).run()
        except Exception as e:
            await self._log_error(sql, normalized, e)
            raise

    async def first(self, sql: str, *params) -> Optional[Any]:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            result = await self._db.prepare(sql).bind(*normalized).first()
            return result if result else None
        except Exception as e:
            await self._log_error(sql, normalized, e)
            raise

    async def all(self, sql: str, *params) -> list:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            result = await self._db.prepare(sql).bind(*normalized).all()
            return result.results if result else []
        except Exception as e:
            await self._log_error(sql, normalized, e)
            raise

    async def _log(self, sql: str, params: tuple) -> None:
        if self._ctx:
            result = self._ctx.log.debug(
                "db.query",
                event_data={"sql": sql[:120], "params": list(params)},
            )
            if inspect.isawaitable(result):
                await result

    async def _log_error(self, sql: str, params: tuple, exc: Exception) -> None:
        msg = f"db.error: {type(exc).__name__}: {exc} | sql={sql[:200]}"
        if self._ctx:
            result = self._ctx.log.error(
                msg,
                event_data={
                    "sql": sql[:200],
                    "params": list(params),
                    "error": str(exc),
                },
            )
            if inspect.isawaitable(result):
                await result
        else:
            print(msg)
