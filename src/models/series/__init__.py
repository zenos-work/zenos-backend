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
    "article_count",
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
    article_count: Optional[int] = 0

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
            article_count=row_get(row, "article_count", 0),
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
    next_article_slug: Optional[str] = None
    prev_article_slug: Optional[str] = None
    parts: Optional[list] = None

    def to_dict(self, scope: str = Scope.LIST) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "part": self.part,
            "total": self.total,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "next_article_slug": self.next_article_slug,
            "prev_article_slug": self.prev_article_slug,
            "parts": self.parts,
        }

    @classmethod
    def from_row(cls, row) -> "ArticleSeriesInfo":
        parts_raw = row_get(row, "all_parts", "")
        parts = []
        next_slug = None
        prev_slug = None
        current_part = row_get(row, "part_number", 1)

        if parts_raw:
            for item in parts_raw.split(","):
                if ":" in item:
                    slug, p_num = item.rsplit(":", 1)
                    p_num = int(p_num)
                    parts.append({"slug": slug, "part": p_num})
                    if p_num == current_part + 1:
                        next_slug = slug
                    elif p_num == current_part - 1:
                        prev_slug = slug

        # Sort parts by number
        parts.sort(key=lambda x: x["part"])

        return cls(
            id=row_get(row, "id"),
            name=row_get(row, "name"),
            part=current_part,
            total=row_get(row, "total_parts", 0),
            description=row_get(row, "description"),
            cover_image_url=row_get(row, "cover_image_url"),
            next_article_slug=next_slug,
            prev_article_slug=prev_slug,
            parts=parts,
        )
