from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get
from models.common.enums import Scope

_LIST_FIELDS = {
    "id",
    "author_id",
    "name",
    "description",
    "cover_image_url",
    "created_at",
    "updated_at",
}
_DETAIL_FIELDS = _LIST_FIELDS


@dataclass
class Series(BaseModel):
    id: str
    author_id: str
    name: str
    created_at: str
    # Fields with defaults must come last
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    updated_at: str = ""

    def to_dict(self, scope: str = Scope.LIST) -> dict:
        allowed = {
            Scope.LIST: _LIST_FIELDS,
            Scope.DETAIL: _DETAIL_FIELDS,
        }.get(scope, _DETAIL_FIELDS)

        result = {}
        for k, v in self.__dict__.items():
            if k in allowed and v is not None:
                result[k] = v
        # Expose `title` as an alias for `name` for forward-compat with TypeScript clients.
        if "name" in result:
            result["title"] = result["name"]
        return result

    @classmethod
    def from_row(cls, row) -> "Series":
        return cls(
            id=row_get(row, "id"),
            author_id=row_get(row, "author_id"),
            name=row_get(row, "name"),
            created_at=row_get(row, "created_at", ""),
            description=row_get(row, "description"),
            cover_image_url=row_get(row, "cover_image_url"),
            updated_at=row_get(row, "updated_at", ""),
        )


@dataclass
class ArticleSeriesInfo(BaseModel):
    """Series info including article's position within series"""

    id: str
    name: str
    part: int
    total: int
    description: Optional[str] = None
    cover_image_url: Optional[str] = None

    def to_dict(self, scope: str = Scope.LIST) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "part": self.part,
            "total": self.total,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
        }

    @classmethod
    def from_row(cls, row) -> "ArticleSeriesInfo":
        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name"),
            part=row_get(row, "part_number"),
            total=row_get(row, "total_parts"),
            description=row_get(row, "description"),
            cover_image_url=row_get(row, "cover_image_url"),
        )
