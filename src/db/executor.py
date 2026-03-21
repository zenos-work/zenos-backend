from typing import Optional, Any


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
        if value is None:
            return None

        # In Python Workers, optional fields may arrive as JS `undefined` proxies.
        to_py = getattr(value, "to_py", None)
        if callable(to_py):
            try:
                value = to_py()
            except TypeError:
                value = to_py(depth=5)

        if value is None:
            return None

        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"undefined", "null"}:
                return None

        return value

    def _normalize_params(self, params: tuple) -> tuple:
        return tuple(self._normalize_param(p) for p in params)

    async def run(self, sql: str, *params) -> None:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            await self._db.prepare(sql).bind(*normalized).run()
        except Exception as e:
            # Here you could add logging of the error, including the SQL and params
            raise e  # Re-raise the exception after logging

    async def first(self, sql: str, *params) -> Optional[Any]:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            result = await self._db.prepare(sql).bind(*normalized).first()
            return result if result else None
        except Exception as e:
            # Here you could add logging of the error, including the SQL and params
            raise e  # Re-raise the exception after logging

    async def all(self, sql: str, *params) -> list:
        normalized = self._normalize_params(params)
        try:
            await self._log(sql, normalized)
            result = await self._db.prepare(sql).bind(*normalized).all()
            return result.results if result else []
        except Exception as e:
            # Here you could add logging of the error, including the SQL and params
            raise e  # Re-raise the exception after logging

    async def _log(self, sql: str, params: tuple) -> None:
        if self._ctx:
            self._ctx.log.debug(
                "db.query",
                event_data={"sql": sql[:120], "params": list(params)},
            )
