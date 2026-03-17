from dataclasses import dataclass
from typing import Optional
from models.base import BaseRequest


@dataclass
class CommentCreateRequest(BaseRequest):
    article_id: str
    content: str
    parent_id: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "CommentCreateRequest":
        article_id = str(data.get("article_id", "")).strip()
        content = str(data.get("content", "")).strip()
        if not article_id:
            raise ValueError("article_id is required")
        if not content:
            raise ValueError("content is required")
        if len(content) > 5000:
            raise ValueError("content must not exceed 5000 characters")
        return cls(
            article_id=article_id,
            content=content,
            parent_id=data.get("parent_id") or data.get("parent_comment_id"),
        )


@dataclass
class CommentUpdateRequest(BaseRequest):
    """
    Why edit exists:
      Authors should be able to fix typos or clarify their comment.
      Only the author can edit their own comment — not even SUPERADMIN.
      Deleted comments cannot be edited (is_deleted=1 guard in SQL).
    """

    content: str

    @classmethod
    def _validate(cls, data: dict) -> "CommentUpdateRequest":
        content = str(data.get("content", "")).strip()
        if not content:
            raise ValueError("content is required")
        if len(content) > 5000:
            raise ValueError("content must not exceed 5000 characters")
        return cls(content=content)


@dataclass
class CommentModerateRequest(BaseRequest):
    """
    Admin moderation of comments.
    - is_hidden: true to hide from articles (spam/abuse)
    - reason: required when hiding
    """

    is_hidden: bool
    reason: Optional[str] = None

    @classmethod
    def _validate(cls, data: dict) -> "CommentModerateRequest":
        is_hidden = data.get("is_hidden", False)
        if not isinstance(is_hidden, bool):
            raise ValueError("is_hidden must be a boolean")
        reason = str(data.get("reason", "")).strip() if data.get("reason") else None
        if is_hidden and not reason:
            raise ValueError("reason required when hiding a comment")
        if reason and len(reason) > 500:
            raise ValueError("reason must not exceed 500 characters")
        return cls(is_hidden=is_hidden, reason=reason)


@dataclass
class CommentDeleteRequest(BaseRequest):
    comment_id: str

    @classmethod
    def _validate(cls, data: dict) -> "CommentDeleteRequest":
        if (
            "comment_id" not in data
            or not isinstance(data["comment_id"], str)
            or not data["comment_id"].strip()
        ):
            raise ValueError("comment_id is required and must be a non-empty string")
        return cls(comment_id=data["comment_id"].strip())
