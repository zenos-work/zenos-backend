from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class ReadingList(BaseModel):
    id: str
    user_id: str
    name: str
    is_public: int
    is_default: int
    article_count: int
    created_at: str
    updated_at: str
    description: Optional[str] = None
    cover_image_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "is_public": bool(self.is_public),
            "is_default": bool(self.is_default),
            "article_count": self.article_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "ReadingList":
        return cls(
            id=row_get(row, "id"),
            user_id=row_get(row, "user_id"),
            name=row_get(row, "name", ""),
            is_public=row_get(row, "is_public", 0),
            is_default=row_get(row, "is_default", 0),
            article_count=row_get(row, "article_count", 0),
            created_at=row_get(row, "created_at", ""),
            updated_at=row_get(row, "updated_at", ""),
            description=row_get(row, "description"),
            cover_image_url=row_get(row, "cover_image_url"),
        )


@dataclass
class ReadingListItem(BaseModel):
    id: str
    list_id: str
    article_id: str
    sort_order: int
    added_at: str
    note: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "list_id": self.list_id,
            "article_id": self.article_id,
            "sort_order": self.sort_order,
            "note": self.note,
            "added_at": self.added_at,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "ReadingListItem":
        return cls(
            id=row_get(row, "id"),
            list_id=row_get(row, "list_id"),
            article_id=row_get(row, "article_id"),
            sort_order=row_get(row, "sort_order", 0),
            added_at=row_get(row, "added_at", ""),
            note=row_get(row, "note"),
        )
