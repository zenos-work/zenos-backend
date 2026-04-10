from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class ArticleRevision(BaseModel):
    id: str
    article_id: str
    version_number: int
    title: str
    content: str
    editor_id: str
    edit_type: str
    word_count: int
    char_diff: int
    created_at: str
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    reading_level: Optional[str] = None
    tags_snapshot: str = "[]"
    change_summary: Optional[str] = None

    def to_dict(self, scope: str = "list") -> dict:
        d = {
            "id": self.id,
            "article_id": self.article_id,
            "version_number": self.version_number,
            "title": self.title,
            "editor_id": self.editor_id,
            "edit_type": self.edit_type,
            "word_count": self.word_count,
            "char_diff": self.char_diff,
            "change_summary": self.change_summary,
            "created_at": self.created_at,
        }
        if scope == "detail":
            d["content"] = self.content
            d["subtitle"] = self.subtitle
            d["cover_image_url"] = self.cover_image_url
            d["reading_level"] = self.reading_level
            d["tags_snapshot"] = self.tags_snapshot
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_row(cls, row) -> "ArticleRevision":
        return cls(
            id=row_get(row, "id"),
            article_id=row_get(row, "article_id"),
            version_number=row_get(row, "version_number", 0),
            title=row_get(row, "title", ""),
            content=row_get(row, "content", ""),
            editor_id=row_get(row, "editor_id", ""),
            edit_type=row_get(row, "edit_type", "manual"),
            word_count=row_get(row, "word_count", 0),
            char_diff=row_get(row, "char_diff", 0),
            created_at=row_get(row, "created_at", ""),
            subtitle=row_get(row, "subtitle"),
            cover_image_url=row_get(row, "cover_image_url"),
            reading_level=row_get(row, "reading_level"),
            tags_snapshot=row_get(row, "tags_snapshot", "[]"),
            change_summary=row_get(row, "change_summary"),
        )
