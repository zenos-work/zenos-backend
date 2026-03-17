from dataclasses import dataclass, field
from typing import Optional
from models.base import BaseModel, row_get
from models.common.enums import Scope

_LIST_FIELDS = {
    "id",
    "title",
    "slug",
    "subtitle",
    "status",
    "author_id",
    "cover_image_url",
    "read_time_minutes",
    "views_count",
    "likes_count",
    "comments_count",
    "is_featured",
    "published_at",
    "created_at",
    "author_name",
    "author_avatar",
    "tags",
}
_DETAIL_FIELDS = _LIST_FIELDS | {"content", "updated_at"}
_ADMIN_FIELDS = _DETAIL_FIELDS | {"rejection_note", "approved_by"}


@dataclass
class Article(BaseModel):
    # FIX: id was int — D1 stores UUIDs as TEXT, must be str
    # FIX: field ordering — all fields without defaults must come first.
    # Python dataclasses raise TypeError if a non-default field follows a default one.
    id: str
    title: str
    slug: str
    status: str
    author_id: str
    views_count: int
    likes_count: int
    comments_count: int
    is_featured: int
    read_time_minutes: int
    created_at: str
    # Fields with defaults must come last
    content: str = ""
    updated_at: str = ""
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    published_at: Optional[str] = None
    rejection_note: Optional[str] = None
    # FIX: approved_by was Optional[int] — should be Optional[str] (UUID)
    approved_by: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    tags: list = field(default_factory=list)

    def to_dict(self, scope: str = Scope.LIST) -> dict:
        allowed = {
            Scope.LIST: _LIST_FIELDS,
            Scope.DETAIL: _DETAIL_FIELDS,
            Scope.ADMIN: _ADMIN_FIELDS,
        }.get(scope, _LIST_FIELDS)
        result = {}
        for k in allowed:
            v = getattr(self, k, None)
            if v is None:
                continue
            # FIX: tags must be serialised as dicts, not raw objects
            result[k] = [t.to_dict() for t in v] if k == "tags" else v
        return result

    @classmethod
    def from_row(cls, row) -> "Article":
        return cls(
            id=row_get(row, "id"),
            title=row_get(row, "title"),
            slug=row_get(row, "slug"),
            status=row_get(row, "status"),
            author_id=row_get(row, "author_id"),
            views_count=row_get(row, "views_count", 0),
            likes_count=row_get(row, "likes_count", 0),
            comments_count=row_get(row, "comments_count", 0),
            is_featured=row_get(row, "is_featured", 0),
            read_time_minutes=row_get(row, "read_time_minutes", 0),
            created_at=row_get(row, "created_at", ""),
            content=row_get(row, "content", ""),
            updated_at=row_get(row, "updated_at", ""),
            subtitle=row_get(row, "subtitle"),
            cover_image_url=row_get(row, "cover_image_url"),
            published_at=row_get(row, "published_at"),
            rejection_note=row_get(row, "rejection_note"),
            approved_by=row_get(row, "approved_by"),
            author_name=row_get(row, "author_name"),
            author_avatar=row_get(row, "author_avatar"),
        )
