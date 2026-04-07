from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import re
from models.base import BaseRequest
from models.common.enums import ArticleContentType


def _normalize_optional_text(value) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == "undefined" or text.lower() == "null":
        return None
    return text


def _normalize_optional_datetime(value, field_name: str) -> Optional[str]:
    text = _normalize_optional_text(value)
    if text is None:
        return None
    # Accept ISO-8601 and normalize to sqlite-friendly UTC string.
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _validate_content_type_slug(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not re.match(r"^[a-z0-9][a-z0-9-]{1,49}$", value):
        raise ValueError(
            "content_type must be lowercase letters/numbers with optional hyphens"
        )
    return value


def _normalize_optional_url_list(value) -> Optional[List[str]]:
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("citations must be an array of URLs")

    cleaned: List[str] = []
    for item in value:
        text = _normalize_optional_text(item)
        if text is None:
            continue
        if not (text.startswith("http://") or text.startswith("https://")):
            raise ValueError("Each citation must be a valid http(s) URL")
        cleaned.append(text)

    if len(cleaned) > 20:
        raise ValueError("citations cannot exceed 20 links")
    return cleaned


@dataclass
class ArticleCreateRequest(BaseRequest):
    """Create a new article (DRAFT status by default)."""

    title: str
    content: str
    subtitle: Optional[str] = None
    content_type: Optional[str] = None
    cover_image_url: Optional[str] = None
    reading_level: Optional[str] = None
    last_verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None
    seo_schema_type: Optional[str] = None
    citations: Optional[List[str]] = None
    tag_ids: List[str] = field(default_factory=list)
    premium_only: int = 0
    premium_teaser_words: int = 300

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

        content_type = _validate_content_type_slug(
            _normalize_optional_text(data.get("content_type"))
        )

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        reading_level = _normalize_optional_text(data.get("reading_level"))
        if reading_level and reading_level not in {
            "Beginner",
            "Intermediate",
            "Advanced",
        }:
            raise ValueError(
                "reading_level must be one of: Beginner, Intermediate, Advanced"
            )

        try:
            last_verified_at = _normalize_optional_datetime(
                data.get("last_verified_at"), "last_verified_at"
            )
            expires_at = _normalize_optional_datetime(
                data.get("expires_at"), "expires_at"
            )
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO-8601 date/time")

        seo_title = _normalize_optional_text(data.get("seo_title"))
        seo_description = _normalize_optional_text(data.get("seo_description"))
        canonical_url = _normalize_optional_text(data.get("canonical_url"))
        og_image_url = _normalize_optional_text(data.get("og_image_url"))
        seo_schema_type = _normalize_optional_text(data.get("seo_schema_type"))
        citations = _normalize_optional_url_list(data.get("citations"))

        if seo_title and len(seo_title) > 160:
            raise ValueError("seo_title cannot exceed 160 characters")
        if seo_description and len(seo_description) > 320:
            raise ValueError("seo_description cannot exceed 320 characters")
        if seo_schema_type and seo_schema_type not in {
            "Article",
            "TechArticle",
            "HowTo",
        }:
            raise ValueError(
                "seo_schema_type must be one of: Article, TechArticle, HowTo"
            )

        tag_ids = data.get("tag_ids", [])
        if not isinstance(tag_ids, list):
            raise ValueError("tag_ids must be a list")
        if len(tag_ids) > 10:
            raise ValueError("Cannot have more than 10 tags per article")

        # Phase 3: Premium fields validation (GAP-015)
        premium_only = data.get("premium_only", 0)
        if premium_only not in (0, 1):
            raise ValueError("premium_only must be 0 or 1")

        premium_teaser_words = data.get("premium_teaser_words", 300)
        if not isinstance(premium_teaser_words, int):
            premium_teaser_words = int(premium_teaser_words)
        if premium_teaser_words < 0 or premium_teaser_words > 2000:
            raise ValueError("premium_teaser_words must be between 0 and 2000")

        return cls(
            title=title,
            content=content,
            subtitle=subtitle if subtitle else None,
            content_type=content_type or ArticleContentType.ARTICLE,
            cover_image_url=cover_image_url,
            reading_level=reading_level,
            last_verified_at=last_verified_at,
            expires_at=expires_at,
            seo_title=seo_title,
            seo_description=seo_description,
            canonical_url=canonical_url,
            og_image_url=og_image_url,
            seo_schema_type=seo_schema_type,
            citations=citations,
            tag_ids=tag_ids,
            premium_only=premium_only,
            premium_teaser_words=premium_teaser_words,
        )


@dataclass
class ArticleUpdateRequest(BaseRequest):
    """Update article (only DRAFT or REJECTED articles can be edited)."""

    title: Optional[str] = None
    content: Optional[str] = None
    subtitle: Optional[str] = None
    content_type: Optional[str] = None
    cover_image_url: Optional[str] = None
    reading_level: Optional[str] = None
    last_verified_at: Optional[str] = None
    expires_at: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_image_url: Optional[str] = None
    seo_schema_type: Optional[str] = None
    citations: Optional[List[str]] = None
    tag_ids: Optional[List[str]] = None
    premium_only: Optional[int] = None
    premium_teaser_words: Optional[int] = None

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

        content_type = _validate_content_type_slug(
            _normalize_optional_text(data.get("content_type"))
        )

        cover_image_url = _normalize_optional_text(data.get("cover_image_url"))

        try:
            last_verified_at = _normalize_optional_datetime(
                data.get("last_verified_at"), "last_verified_at"
            )
            expires_at = _normalize_optional_datetime(
                data.get("expires_at"), "expires_at"
            )
        except ValueError:
            raise ValueError("Invalid datetime format. Use ISO-8601 date/time")

        seo_title = _normalize_optional_text(data.get("seo_title"))
        seo_description = _normalize_optional_text(data.get("seo_description"))
        canonical_url = _normalize_optional_text(data.get("canonical_url"))
        og_image_url = _normalize_optional_text(data.get("og_image_url"))
        seo_schema_type = _normalize_optional_text(data.get("seo_schema_type"))
        citations = _normalize_optional_url_list(data.get("citations"))

        if seo_title is not None and len(seo_title) > 160:
            raise ValueError("seo_title cannot exceed 160 characters")
        if seo_description is not None and len(seo_description) > 320:
            raise ValueError("seo_description cannot exceed 320 characters")
        if seo_schema_type is not None and seo_schema_type not in {
            "Article",
            "TechArticle",
            "HowTo",
        }:
            raise ValueError(
                "seo_schema_type must be one of: Article, TechArticle, HowTo"
            )

        tag_ids = data.get("tag_ids")

        reading_level = _normalize_optional_text(data.get("reading_level"))
        if reading_level is not None and reading_level not in {
            "Beginner",
            "Intermediate",
            "Advanced",
        }:
            raise ValueError(
                "reading_level must be one of: Beginner, Intermediate, Advanced"
            )
        if tag_ids is not None:
            if not isinstance(tag_ids, list):
                raise ValueError("tag_ids must be a list")
            if len(tag_ids) > 10:
                raise ValueError("Cannot have more than 10 tags per article")

        # Phase 3: Premium fields validation (GAP-015)
        premium_only = data.get("premium_only")
        if premium_only is not None and premium_only not in (0, 1):
            raise ValueError("premium_only must be 0 or 1")

        premium_teaser_words = data.get("premium_teaser_words")
        if premium_teaser_words is not None:
            if not isinstance(premium_teaser_words, int):
                premium_teaser_words = int(premium_teaser_words)
            if premium_teaser_words < 0 or premium_teaser_words > 2000:
                raise ValueError("premium_teaser_words must be between 0 and 2000")

        return cls(
            title=title,
            content=content,
            subtitle=subtitle,
            content_type=content_type,
            cover_image_url=cover_image_url,
            reading_level=reading_level,
            last_verified_at=last_verified_at,
            expires_at=expires_at,
            seo_title=seo_title,
            seo_description=seo_description,
            canonical_url=canonical_url,
            og_image_url=og_image_url,
            seo_schema_type=seo_schema_type,
            citations=citations,
            tag_ids=tag_ids,
            premium_only=premium_only,
            premium_teaser_words=premium_teaser_words,
        )


@dataclass
class RejectArticleRequest(BaseRequest):
    """Reject submitted article with mandatory feedback."""

    note: str

    @classmethod
    def _validate(cls, data: dict) -> "RejectArticleRequest":
        note = data.get("note") or data.get("reason")
        if not note:
            raise ValueError("Rejection note is required")
        note = str(note).strip()
        if len(note) < 10:
            raise ValueError("Rejection note must be at least 10 characters")
        if len(note) > 1000:
            raise ValueError("Rejection note cannot exceed 1000 characters")
        return cls(note=note)
