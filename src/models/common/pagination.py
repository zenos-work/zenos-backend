from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel


@dataclass
class PaginatedResponse(BaseModel):
    """
    Generic paginated wrapper — ALL list endpoints return this.
    Shape: { items, page, limit, has_more, total }
    """

    items: list
    page: int
    limit: int
    has_more: bool = False
    total: Optional[int] = None
    scope: str = "list"

    def to_dict(self, scope: str = None) -> dict:
        effective = scope or self.scope
        return {
            "items": [
                i.to_dict(effective) if isinstance(i, BaseModel) else i
                for i in self.items
            ],
            "page": self.page,
            "limit": self.limit,
            "has_more": self.has_more,
            "total": self.total,
        }

    @classmethod
    def of(
        cls, items: list, page: int, limit: int, total: int = None, scope: str = "list"
    ) -> "PaginatedResponse":
        return cls(
            items=items,
            page=page,
            limit=limit,
            has_more=len(items) == limit,
            total=total,
            scope=scope,
        )
