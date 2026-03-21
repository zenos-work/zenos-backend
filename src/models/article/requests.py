from dataclasses import dataclass, field
from typing import Optional, List
from models.base import BaseRequest


def _normalize_optional_text(value) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == "undefined" or text.lower() == "null":
        return None
    return text


@dataclass
class ArticleCreateRequest(BaseRequest):
    """Create a new article (DRAFT status by default)."""

    title: str
    content: str
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    tag_ids: List[str] = field(default_factory=list)

    @classmethod
    def _validate(cls, data: dict) -> "ArticleCreateRequest":
        title = data.get("title")
        if not title:
            raise ValueError("Title is required")
        title = str(title).strip()
        if len(title) < 5:
            raise ValueError("Title must be at least 5 characters")
        if len(title) > 200:
            raise ValueError("Title cannot be longer than 200 characters")

        content = data.get("content")
        if not content:
            raise ValueError("Content is required")
        content = str(content).strip()
        if len(content) < 50:
            raise ValueError("Content must be at least 50 characters long")
        if len(content) > 50000:
            raise ValueError("Content cannot exceed 50,000 characters")

        subtitle = _normalize_optional_text(data.get("subtitle"))
        if subtitle:
            if len(subtitle) > 500:
                raise ValueError("Subtitle cannot be longer than 500 characters")

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        tag_ids = data.get("tag_ids", [])
        if not isinstance(tag_ids, list):
            raise ValueError("tag_ids must be a list")
        if len(tag_ids) > 10:
            raise ValueError("Cannot have more than 10 tags per article")

        return cls(
            title=title,
            content=content,
            subtitle=subtitle if subtitle else None,
            cover_image_url=cover_image_url,
            tag_ids=tag_ids,
        )


@dataclass
class ArticleUpdateRequest(BaseRequest):
    """Update article (only DRAFT or REJECTED articles can be edited)."""

    title: Optional[str] = None
    content: Optional[str] = None
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    tag_ids: Optional[List[str]] = None

    @classmethod
    def _validate(cls, data: dict) -> "ArticleUpdateRequest":
        # All fields optional on update
        title = data.get("title")
        if title is not None:
            title = str(title).strip()
            if len(title) < 5:
                raise ValueError("Title must be at least 5 characters")
            if len(title) > 200:
                raise ValueError("Title cannot be longer than 200 characters")

        content = data.get("content")
        if content is not None:
            content = str(content).strip()
            if len(content) < 50:
                raise ValueError("Content must be at least 50 characters long")
            if len(content) > 50000:
                raise ValueError("Content cannot exceed 50,000 characters")

        subtitle = _normalize_optional_text(data.get("subtitle"))
        if subtitle is not None:
            if len(subtitle) > 500:
                raise ValueError("Subtitle cannot be longer than 500 characters")

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        tag_ids = data.get("tag_ids")
        if tag_ids is not None:
            if not isinstance(tag_ids, list):
                raise ValueError("tag_ids must be a list")
            if len(tag_ids) > 10:
                raise ValueError("Cannot have more than 10 tags per article")

        return cls(
            title=title,
            content=content,
            subtitle=subtitle,
            cover_image_url=cover_image_url,
            tag_ids=tag_ids,
        )


@dataclass
class RejectArticleRequest(BaseRequest):
    """Reject submitted article with mandatory feedback."""

    note: str

    @classmethod
    def _validate(cls, data: dict) -> "RejectArticleRequest":
        note = data.get("note")
        if not note:
            raise ValueError("Rejection note is required")
        note = str(note).strip()
        if len(note) < 10:
            raise ValueError("Rejection note must be at least 10 characters")
        if len(note) > 1000:
            raise ValueError("Rejection note cannot exceed 1000 characters")
        return cls(note=note)
