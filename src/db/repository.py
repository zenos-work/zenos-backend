from typing import Optional, Any, Type, Protocol
from db.executor import D1Executor
from models.base import BaseModel


class IRepository(Protocol):
    """
    Contract every repository must satisfy.
    Allows handler/service tests to inject mock repositories.
    """

    async def find_one(self, sql: str, *params) -> Optional[Any]: ...
    async def find_all(self, sql: str, *params) -> list: ...
    async def execute(self, sql: str, *params) -> None: ...


class BaseRepository:
    """
    Base class for all entity repositories.
    Subclasses get D1Executor for free and only need to
    implement the row-mapping methods specific to their entity.

    Rules:
      - Never write SQL here — use queries.py constants
      - Never add business logic — that belongs in service.py
      - Always map rows via map_one() / map_many()
    """

    def __init__(self, db, ctx=None):
        self._ex = D1Executor(db, ctx)

    async def find_one(self, sql: str, *params) -> Optional[Any]:
        return await self._ex.first(sql, *params)

    async def find_all(self, sql: str, *params) -> list:
        return await self._ex.all(sql, *params)

    async def execute(self, sql: str, *params) -> None:
        await self._ex.run(sql, *params)

    def map_one(self, row, model_cls: Type[BaseModel]):
        """Map a single row to a model instance, or return None."""
        return model_cls.from_row(row) if row else None

    def map_many(self, rows: list, model_cls: Type[BaseModel]) -> list:
        """Map a list of rows to model instances."""
        return [model_cls.from_row(r) for r in rows]
