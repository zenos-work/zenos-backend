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
    user_id: Optional[str] = None
    actor_id: Optional[str] = None
    article_id: Optional[str] = None
    comment_id: Optional[str] = None
    channel: str = "in_app"
    delivery_status: str = "pending"
    delivered_at: Optional[str] = None
    external_ref: Optional[str] = None
    group_key: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Notification":
        return cls(
            id=row_get(row, "id"),
            type=row_get(row, "type"),
            message=row_get(row, "message"),
            is_read=row_get(row, "is_read", 0),
            created_at=row_get(row, "created_at"),
            user_id=row_get(row, "user_id"),
            actor_id=row_get(row, "actor_id"),
            article_id=row_get(row, "article_id"),
            comment_id=row_get(row, "comment_id"),
            channel=row_get(row, "channel", "in_app"),
            delivery_status=row_get(row, "delivery_status", "pending"),
            delivered_at=row_get(row, "delivered_at"),
            external_ref=row_get(row, "external_ref"),
            group_key=row_get(row, "group_key"),
        )
