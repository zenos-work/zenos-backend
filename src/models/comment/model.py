from dataclasses import dataclass, field
from typing import Optional, List
from models.base import BaseModel, row_get


@dataclass
class Comment(BaseModel):
    id: str
    article_id: str
    author_id: str
    is_deleted: int
    created_at: str
    # Fields with defaults
    content: str = ""
    updated_at: Optional[str] = None
    parent_id: Optional[str] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    replies: List["Comment"] = field(default_factory=list)
    # Moderation fields
    is_hidden: int = 0
    moderation_reason: Optional[str] = None
    moderated_by: Optional[str] = None
    moderated_at: Optional[str] = None
    flag_count: int = 0

    def to_dict(self, scope: str = "default") -> dict:
        """
        Scope 'default': Public view (hides moderation details)
        Scope 'admin': Full moderation details for admins
        """
        content = "[deleted]" if self.is_deleted else self.content
        if self.is_hidden and scope != "admin":
            content = "[removed by moderator]"

        base_dict = {
            "id": self.id,
            "article_id": self.article_id,
            "author_id": self.author_id,
            "parent_id": self.parent_id,
            "content": content,
            "is_deleted": self.is_deleted,
            "is_hidden": self.is_hidden,
            "author_name": self.author_name,
            "author_avatar": self.author_avatar,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "flag_count": self.flag_count,
            "replies": [r.to_dict(scope) for r in self.replies],
        }

        if scope == "admin":
            base_dict.update(
                {
                    "moderation_reason": self.moderation_reason,
                    "moderated_by": self.moderated_by,
                    "moderated_at": self.moderated_at,
                }
            )

        return base_dict

    @classmethod
    def from_row(cls, row) -> "Comment":
        return cls(
            id=row_get(row, "id"),
            article_id=row_get(row, "article_id"),
            author_id=row_get(row, "author_id"),
            is_deleted=row_get(row, "is_deleted", 0),
            created_at=row_get(row, "created_at", ""),
            content=row_get(row, "content", ""),
            updated_at=row_get(row, "updated_at"),
            parent_id=row_get(row, "parent_id"),
            author_name=row_get(row, "author_name"),
            author_avatar=row_get(row, "author_avatar"),
            is_hidden=row_get(row, "is_hidden", 0),
            moderation_reason=row_get(row, "moderation_reason"),
            moderated_by=row_get(row, "moderated_by"),
            moderated_at=row_get(row, "moderated_at"),
            flag_count=row_get(row, "flag_count", 0),
        )
