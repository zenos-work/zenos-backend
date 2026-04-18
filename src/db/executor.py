import inspect
from typing import Optional, Any

try:
    import js

    js_null = js.JSON.parse("null") if hasattr(js, "JSON") else None
except ImportError:
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

    def _normalize_param(self, value: Any) -> Any:
        # Check for Pyodide JsProxy objects. These can sometimes wrap 'undefined'
        # which D1 rejects. We check string representation as a heuristic.
        proxy_type = type(value).__name__
        if "JsProxy" in proxy_type or "JsObject" in proxy_type:
            try:
                rendered = str(value).strip()
                if rendered in (
                    "undefined",
                    "null",
                    "[object Undefined]",
                    "[object Null]",
                ):
                    return js_null
                # Try to convert proxy back to Python primitive if possible
                to_py = getattr(value, "to_py", None)
                if callable(to_py):
                    try:
                        value = to_py()
                    except (TypeError, ValueError):
                        value = to_py(depth=2)
            except Exception:
                return js_null

        if value is None:
            return None

        # Handle strings that look like JS nulls
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in ("undefined", "null", "[object undefined]", "[object null]"):
                return None
            return value

        primitive_types = (int, float, bool, bytes, bytearray, memoryview)
        if isinstance(value, primitive_types):
            return value

        # Normalize non-string objects by their string representation when possible.
        try:
            rendered = str(value).strip()
            if rendered.lower() in (
                "undefined",
                "null",
                "[object undefined]",
                "[object null]",
            ):
                return None
        except Exception:
            pass

        # Last-resort fallback: attempt string conversion or return None
        try:
            return str(value)
        except Exception:
            return js_null

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
