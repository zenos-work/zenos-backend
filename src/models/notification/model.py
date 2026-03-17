from dataclasses import dataclass
from typing import Optional
from models.base import BaseModel, row_get


@dataclass
class Notification(BaseModel):
    id: str
    type: str
    message: str
    is_read: int
    created_at: str
    actor_id: Optional[str] = None
    article_id: Optional[str] = None
    comment_id: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Notification":
        return cls(
            id=row_get(row, "id"),
            type=row_get(row, "type"),
            message=row_get(row, "message"),
            is_read=row_get(row, "is_read", 0),
            created_at=row_get(row, "created_at"),
            actor_id=row_get(row, "actor_id"),
            article_id=row_get(row, "article_id"),
            comment_id=row_get(row, "comment_id"),
        )
