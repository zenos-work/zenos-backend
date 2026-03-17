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

    async def run(self, sql: str, *params) -> None:
        try:
            await self._log(sql, params)
            await self._db.prepare(sql).bind(*params).run()
        except Exception as e:
            # Here you could add logging of the error, including the SQL and params
            raise e  # Re-raise the exception after logging

    async def first(self, sql: str, *params) -> Optional[Any]:
        try:
            await self._log(sql, params)
            result = await self._db.prepare(sql).bind(*params).first()
            return result if result else None
        except Exception as e:
            # Here you could add logging of the error, including the SQL and params
            raise e  # Re-raise the exception after logging

    async def all(self, sql: str, *params) -> list:
        try:
            await self._log(sql, params)
            result = await self._db.prepare(sql).bind(*params).all()
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
